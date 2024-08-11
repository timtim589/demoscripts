import argparse
import tarfile
import tempfile
import os

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

parser = argparse.ArgumentParser(prog="StorageDownload",
                                 description="Programm to download all blobs from an Azure StorageAccount")
parser.add_argument("storageaccount_name", help="The name of the StorageAccount to enumerate.", type=str)
parser.add_argument("output_filename", help="The path + filename where the script should deposit the tar file.", type=str)
args = parser.parse_args()

def download_storageaccount(storageaccount_name: str, output_location: str):
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
    with tarfile.open(output_location, "w:gz") as tar:
        tar.add(temp_dir.name, arcname=os.path.basename(temp_dir.name))
    temp_dir.cleanup()

account_to_download = args.storageaccount_name
output_filename = args.output_filename
download_storageaccount(account_to_download, output_filename)
