"""
Author: Horo
URL: https://github.com/scare376/Kavita-Scripts
Date created: June 15, 2024
Updated: June 19

Description:
This will change the language of every series in a library you choose to whatever language you choose. It will first
give you a list of your libraries to choose from, then give you a list of supported languages to choose from, and
finally will set every series to that language you chose.
Made using DieselTech's scan_all_libraries script as a base with some help from them as well.

Software requirements:
- Python 3 or later
- requests
- json

Usage:
python update_library_language.py
"""
import requests
import json
from urllib.parse import urlparse

url = input("Paste in your full ODPS URL from your Kavita user dashboard (/preferences#clients): ")

parsed_url = urlparse(url)

host_address = parsed_url.scheme + "://" + parsed_url.netloc
api_key = parsed_url.path.split('/')[-1]

print("Host Address:", host_address)
print("API Key:", api_key)

login_endpoint = "/api/Plugin/authenticate"
library_endpoint = "/api/Library/libraries"
series_endpoint = "/api/Series/all-v2"
lang_endpoint = "/api/Metadata/all-languages"
series_metadata_endpoint = "/api/Series/metadata"
try:
    apikeylogin = requests.post(host_address + login_endpoint + "?apiKey=" + api_key + "&pluginName=pythonScanScript")
    apikeylogin.raise_for_status()  # check if the response code indicates an error
    jwt_token = apikeylogin.json()['token']
#    print("JWT Token:", jwt_token) # Only for debug 
except requests.exceptions.RequestException as e:
    print("Error during authentication:", e)
    exit()

headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
lib_response = requests.get(host_address + library_endpoint, headers=headers)  #Pull the list of Libraries

if lib_response.status_code == 200:
    lib_data = lib_response.json()
    for item in lib_data:
        lib_id = item["id"]
        name = item["name"]
        print(f"Library name: {name} id: {lib_id}")
else:
    print("Error: Failed to retrieve data from the API.")

lib_choice = int(input("Which Library id do you want to update the language on?"))

lang_response = requests.get(host_address + lang_endpoint, headers=headers)  #Pull the list of languages that Kavita accepts

if lang_response.status_code == 200:
    lang_data = lang_response.json()
    for item in lang_data:
        isoCode = item["isoCode"]
        title = item["title"]
        print(f"title: {title} isoCode: {isoCode}")
else:
    print("Error: Failed to retrieve data from the API.")

languageInput = input("What language code do you want to insert?")
filterDto = {'libraries': lib_choice, 'sortOptions': {"sortField": 1, "isAscending": True}}

series_response = requests.post(host_address + series_endpoint + "?PageNumber=1&PageSize=0&libraryId=" + str(lib_choice), headers=headers, json=filterDto)  #Pull all the series within Kavita

if series_response.status_code == 200:
    series_data = series_response.json()
    for item in series_data:
        series_id = item["id"]
        series_name = item["name"]
        library_id = item["libraryId"]
        if library_id == lib_choice:  #This is needed in order to only select the series within the library you chose. Otherwise, it doesn't get filtered because adding libraries to the json and the libraryId to the URL does nothing.
            series_metadata_get_response = requests.get(host_address + series_metadata_endpoint + "?seriesId=" + str(series_id), headers=headers)  #Pulls the metadata for the series so that we can add the language metadata that we want. We're also going to lock the field so that it can't be edited by a normal scan.
            if series_metadata_get_response.status_code == 200:
                series_metadata_data = series_metadata_get_response.json()
                series_metadata_data["language"] = languageInput
                series_metadata_data["languageLocked"] = True
                series_metadata_post_response = requests.post(host_address + series_metadata_endpoint, headers=headers, json={"seriesMetadata":series_metadata_data})  #Pushes the updated metadata json.
                if series_metadata_post_response.status_code == 200:
                    new_series_metadata_get_response = requests.get(host_address + series_metadata_endpoint + "?seriesId=" + str(series_id), headers=headers)  #Final pull to confirm that everything worked correctly
                    if new_series_metadata_get_response.status_code == 200:
                        new_series_metadata_data = new_series_metadata_get_response.json()
                        newLanguage = new_series_metadata_data["language"]
                        print(f"Series name: {series_name} id: {series_id} language: {newLanguage}")
else:
    print("Error: Failed to retrieve data from the API.")
