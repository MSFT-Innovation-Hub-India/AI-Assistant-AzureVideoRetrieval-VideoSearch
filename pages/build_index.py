import requests
from dotenv import load_dotenv
import os
import pandas as pd
import uuid
import json
import streamlit as st

load_dotenv()

from azure.storage.blob import (
    generate_container_sas,
    ContainerSasPermissions,
    BlobServiceClient
)
import datetime
import time

# Streamlit App
st.title("Index creation - Video Retrieval Service")

# Add a description text area
description = "This page is used to create an index in the Video Retrieval Service and indexes the videos."
st.text_area("Description", description, height=70, disabled=True)



warning = "Run this program only once to create the index and populating it the first time. Running it again will create duplicate content in the index."
st.markdown(f'<div style="background-color: red; padding: 3px;">{warning}</div>', unsafe_allow_html=True)

st.markdown("---")

# Replace with your Azure Video Indexer credentials
az_video_indexer_endpoint = os.getenv("az-video-indexer-endpoint")
az_video_indexer_index_name = os.getenv("az-video-indexer-index-name")
az_video_indexer_api_version = os.getenv("az-video-indexer-api-version")
az_video_indexer_key = os.getenv("az-video-indexer-key")

az_storage_account_name = os.getenv("az-storage-account-name")
az_storage_container_name = os.getenv("az-storage-container-name")
az_storage_account_key = os.getenv("az-storage-account-key")

def build_index():
    # use Azure Storage python SDK to generate a SAS token for the container
    sas_token = generate_container_sas(
        account_name=az_storage_account_name,
        container_name=az_storage_container_name,
        account_key=az_storage_account_key,
        permission=ContainerSasPermissions(read=True, write=True),
        expiry=datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1),
    )
    index_url = f"https://{az_video_indexer_endpoint}/computervision/retrieval/indexes/{az_video_indexer_index_name}?api-version={az_video_indexer_api_version}"
    index_headers = {
        "Ocp-Apim-Subscription-Key": az_video_indexer_key,
        "Content-Type": "application/json",
    }
    index_payload = {
        "metadataSchema": {
            "fields": [
                {
                    "name": "cameraId",
                    "searchable": False,
                    "filterable": True,
                    "type": "string"
                },
                {
                    "name": "timestamp",
                    "searchable": False,
                    "filterable": True,
                    "type": "datetime"
                }
            ]
        },
        "features": [
            {
                "name": "vision"
            },
            {
                "name": "speech"
            }
        ]
    }

    index_response = None
    
    with st.spinner("Creating video index..."):
        index_response = requests.put(index_url, headers=index_headers, json=index_payload)

        if index_response.status_code == 200 | index_response.status_code == 201:
            st.write("Video index successfully created.")
        else:
            if index_response.status_code == 409:
                st.write("Video index already exists. Proceeding to ingest videos.")
            else:
                st.write("Failed to create video index.")
                st.write(index_response.json())
                return
    
    
    # Create a blob service client to interact with the container
    blob_service_client = BlobServiceClient.from_connection_string(
        f"DefaultEndpointsProtocol=https;AccountName={az_storage_account_name};AccountKey={az_storage_account_key};EndpointSuffix=core.windows.net"
    )

    # Call the Azure Video Indexer API to index the video
    url = f"https://{az_video_indexer_endpoint}/computervision/retrieval/indexes/{az_video_indexer_index_name}/ingestions/{uuid.uuid4()}?api-version={az_video_indexer_api_version}"
    headers = {
            "Ocp-Apim-Subscription-Key": az_video_indexer_key,
            "Content-Type": "application/json",
        }


    payload = {
            "videos": [
            ]
        }
    # Iterate over the blobs in the container and build the index
    for blob in blob_service_client.get_container_client(az_storage_container_name).list_blobs():
        blob_name = blob.name
        blob_url = f"https://{az_storage_account_name}.blob.core.windows.net/{az_storage_container_name}/{blob_name}"
        st.write(f"Processing blob: {blob_name}")
        
        sas_url = (
                blob_url + "?"+sas_token
            )

        payload["videos"].append(
            {
                "mode": "add",
                "documentId": str(uuid.uuid4()),
                "documentUrl": sas_url,
                "metadata": {
                "cameraId": "video-indexer-demo-camera1",
                "timestamp": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        )

    response = requests.put(url, headers=headers, json=payload)
    if response.status_code == 202:
        st.write(f"Video  indexing job successfully triggered.")
        st.write('---- the ingestion response ----\n', response.json())
        job_status = "running"
        
        with st.spinner("Indexing in progress..."):
            while job_status == "running":
                url = f"https://{az_video_indexer_endpoint}/computervision/retrieval/indexes/{az_video_indexer_index_name}/ingestions"
                headers = {
                        "Ocp-Apim-Subscription-Key": az_video_indexer_key
                    }
                # Define the parameters
                params = {
                    "$top": 20,
                    "api-version": az_video_indexer_api_version
                }
                # curl.exe -v -X GET "https://<YOUR_ENDPOINT_URL>/computervision/retrieval/indexes/my-video-index/ingestions?api-version=2023-05-01-preview&$top=20"
                # check the status of the ingestion job
                response = requests.get(url, headers=headers, params=params)
                current_status =  ((json.loads(response.text))["value"][0]["state"]).lower()
                if current_status == "running":
                    time.sleep(3)
                else:
                    st.write("Ingestion job state is ", current_status)
                    if (current_status != "completed"):
                        st.write("Ingestion job failed.")
                        st.write(response.json())
                        return
                    else:
                        st.write("Ingestion job completed successfully.")
                    job_status = current_status
    else:
        st.write(f"Failed to start ingestion job for the videos.")
        st.write(response.json())

# Add a button to call the build_index function
if st.button("Start Indexing"):
    build_index()