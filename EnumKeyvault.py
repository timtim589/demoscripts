#!/usr/bin/env python3

import argparse
import json
import requests
from azure.identity import DefaultAzureCredential

parser = argparse.ArgumentParser(prog="KeyvaultEnum",
                                 description="Programm to enumerate Azure KeyVaults")
parser.add_argument("keyvault_name", help="The name of the Keyvault to enumerate.", type=str)
args = parser.parse_args()

def enum_vault(keyvault_name:str):
    """Enumerates all secrets of a given vault"""
    print(f"Starting enumeration of {keyvault_name}")
    enumerated_secrets = []
    base_url = f"https://{keyvault_name}.vault.azure.net"
    credential = DefaultAzureCredential()
    token = credential.get_token("https://vault.azure.net").token
    headers = {"Authorization": f"Bearer {token}"}
    url = base_url + "/secrets?api-version=7.4"
    response = requests.get(url=url, headers=headers)
    if response.status_code == 200:
        secrets = response.json()['value']
        for secret in secrets:
            url = secret['id'] + "?api-version=7.4"
            response = requests.get(url=url, headers=headers)
            if response.status_code == 200:
                enumerated_secrets.append(response.json())
            else:
                print("Failed to get secret")
    else:
        print("Failed to list secrets")
    return json.dumps(enumerated_secrets)

vault_to_enum = args.keyvault_name
results = enum_vault(vault_to_enum)
print(results)
