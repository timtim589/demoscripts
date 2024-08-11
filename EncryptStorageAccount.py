import argparse
from cryptography.fernet import Fernet
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

parser = argparse.ArgumentParser(prog="StorageEncryption",
                                 description="Programm to encrypt all blobs in an Azure StorageAccount")
parser.add_argument("storageaccount_name", help="The name of the StorageAccount to enumerate.", type=str)
parser.add_argument("encryption_key", help="The key used to encrypt the data.", type=str)
parser.add_argument("action", help="The action to take on the data: encrypt or decrypt.", type=str)
args = parser.parse_args()

def encrypt(message: str, key: bytes) -> bytes:
    """ A function to encrypt a given value """
    message = message.encode()
    return Fernet(key).encrypt(message)

def decrypt(token: bytes, key: bytes) -> str:
    """ A function to decypt a given value"""
    message = Fernet(key).decrypt(token)
    return message.decode()

def alter_storageaccount(storageaccount_name: str, key: bytes, data_action: str):
    """ A function which encrypts the storage account using a key. """
    account_url = f"https://{storageaccount_name}.blob.core.windows.net"
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url, credential=credential)
    containers = blob_service_client.list_containers()
    for container in containers:
        containerclient = blob_service_client.get_container_client(container=container.name)
        blobs = containerclient.list_blobs()
        for blob in blobs:
            if data_action == "encrypt":
                blobclient = containerclient.get_blob_client(blob.name)
                blobdata = (blobclient.download_blob(max_concurrency=1, encoding='UTF-8')).readall()
                encrypteddata = encrypt(blobdata, key)
                blobclient.upload_blob(data=encrypteddata, overwrite=True)
                print(f"Successfully encrypted blob {blob.name}!")
            elif data_action == "decrypt":
                blobclient = containerclient.get_blob_client(blob.name)
                blobdata = (blobclient.download_blob(max_concurrency=1, encoding='UTF-8')).readall()
                encrypteddata = decrypt(blobdata, key)
                blobclient.upload_blob(data=encrypteddata, overwrite=True)
                print(f"Successfully decrypted blob {blob.name}!")

account_to_encrypt = args.storageaccount_name
encryption_key = (args.encryption_key).encode()
action = args.action
alter_storageaccount(account_to_encrypt, encryption_key, action)
