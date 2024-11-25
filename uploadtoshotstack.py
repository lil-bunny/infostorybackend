from fastapi import FastAPI, UploadFile, File, HTTPException
from firebase_admin import credentials, initialize_app, storage
import firebase_admin
import requests
import uuid
import os
import json
import time
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Firebase initialization
BUCKET_NAME = os.getenv('FIREBASE_BUCKET_NAME')
FIREBASE_CREDS = os.getenv('FIREBASE_CREDENTIALS_PATH')
SHOTSTACK_API_KEY = os.getenv('SHOTSTACK_API_KEY')
SHOTSTACK_API_URL = os.getenv('SHOTSTACK_API_URL', "https://api.shotstack.io/ingest/stage")

# Firebase initialization with environment variables
cred = credentials.Certificate(FIREBASE_CREDS)
firebaseapp = initialize_app(cred, {
    'storageBucket': BUCKET_NAME
})

class UploadResponse(BaseModel):
    success: bool
    message: str
    video_url: Optional[str] = None
    source_id: Optional[str] = None

async def upload_to_firebase(file: UploadFile) -> str:
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}.mp4"
        
        # Get bucket
        bucket = storage.bucket()
        
        # Create blob
        blob = bucket.blob(f"videos/{unique_filename}")
        
        # Upload file
        contents = await file.read()
        blob.upload_from_string(
            contents,
            content_type=file.content_type
        )
        
        # Make public and get URL
        blob.make_public()
        return blob.public_url
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firebase upload failed: {str(e)}")

async def submit_to_shotstack(video_url: str) -> dict:
    try:
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': SHOTSTACK_API_KEY
        }
        
        payload = {
            "url": video_url,
        }
        
        response = requests.post(
            f"{SHOTSTACK_API_URL}/sources",
            headers=headers,
            json=payload
        )
        print(response.json())
        
        return response.json()
    
    except Exception as e:
        raise HTTPException(status_code=500, 
                          detail=f"Shotstack API call failed: {str(e)}")

async def check_shotstack_status(source_id: str) -> dict:
    try:
        headers = {
            'Accept': 'application/json',
            'x-api-key': SHOTSTACK_API_KEY
        }
        
        response = requests.get(
            f"{SHOTSTACK_API_URL}/sources/{source_id}",
            headers=headers
        )
        print(response.json())
            
        return response.json()
    
    except Exception as e:
        raise HTTPException(status_code=500, 
                          detail=f"Status check failed: {str(e)}")

@app.post("/upload-video/", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)):
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        firebase_url = await upload_to_firebase(file)
        print(f"firebase={firebase_url}")
        
        shotstack_response = await submit_to_shotstack(firebase_url)
        source_id = shotstack_response['data']['id']
        
        max_attempts = 30  # 5 minutes timeout (10 second intervals)
        attempts = 0
        
        while attempts < max_attempts:
            status_response = await check_shotstack_status(source_id)
            status = status_response['data']['attributes']['status']
           
            if status == 'ready':
                video_url = status_response['data']['attributes']['source']
                return UploadResponse(
                    success=True,
                    message="Video processed successfully",
                    video_url=video_url,
                    source_id=source_id
                )
            elif status == 'failed':
                raise HTTPException(status_code=500, 
                                  detail="Video processing failed")
            
            attempts += 1
            time.sleep(10)
        
        return UploadResponse(
            video_url=video_url,
            success=True,
            message="Video uploaded but processing is still ongoing",
            source_id=source_id
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, 
                          detail=f"Upload process failed: {str(e)}")

@app.get("/check-status/{source_id}", response_model=UploadResponse)
async def check_status(source_id: str):
    try:
        status_response = await check_shotstack_status(source_id)
        status = status_response['data']['attributes']['status']
        
        if status == 'ready':
            video_url = status_response['data']['attributes']['source']
            return UploadResponse(
                success=True,
                message="Video processing complete",
                video_url=video_url,
                source_id=source_id
            )
        elif status == 'failed':
            return UploadResponse(
                success=False,
                message="Video processing failed",
                source_id=source_id
            )
        else:
            return UploadResponse(
                success=True,
                message=f"Video processing status: {status}",
                source_id=source_id
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, 
                          detail=f"Status check failed: {str(e)}")
