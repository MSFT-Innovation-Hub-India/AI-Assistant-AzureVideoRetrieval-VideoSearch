# Multimodal video search

This sample Application showcases how one could:
- Create an index in Video Indexer Service and ingest videos from a video library in Azure Blob Store into it.
- perform multi modal search across videos in a catalog. Users could search based on visual cues in the video, or based on speech in the video. There is no pre-requisite for transcriptions to be available in the video

## Services used

An Azure Cognitive Services multi-service account is used for Video Retrieval. It is used to index the Videos for search. The Videos are ingested based on their URL (location) inside an Azure Blob Storage Container. These could reside anywhere else too as long as they can be accessed through a url.
Once ingested, the Video Retrieval Service allows for search based on visual or speech cues from the user

**Note! Before running the application, ensure that key access is enabled on the Azure Blob Storage Account. This program will fail if that is disabled.**

A .env file needs to be created in the root folder, with the configuration elements below:

```
az-video-indexer-endpoint="<>.cognitiveservices.azure.com"
az-video-indexer-key=""
az-video-indexer-index-name="m365copilotvideos"
az-video-indexer-api-version="2023-05-01-preview"
az-storage-account-name="<>"
az-storage-container-name="m365copilotdemos"
az-storage-account-key=""
```
### Using the Sample Application

#### Creating an index

Navigate to the 'build index' page to create and populate the index
Note: You must run this only once when building the index the first time. Run once again will create duplicate content in the same index

#### Searching for videos
The user could select whether they would like to search based on visual or speech cues, and provide their input.
The Video Retrieval Service returns the videos that contain matching frames along with the timestamp when they occur during the video
