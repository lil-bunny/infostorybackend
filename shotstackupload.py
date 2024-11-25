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

# Configuration variables
BUCKET_NAME = os.getenv('FIREBASE_BUCKET_NAME')
SHOTSTACK_API_KEY = os.getenv('SHOTSTACK_API_KEY')
SHOTSTACK_API_URL = os.getenv('SHOTSTACK_API_URL', 'https://api.shotstack.io/ingest/stage')
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')

# Firebase initialization
if not all([BUCKET_NAME, FIREBASE_CREDENTIALS_PATH]):
    raise ValueError("Missing required environment variables for Firebase configuration")

cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
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
    if not SHOTSTACK_API_KEY:
        raise ValueError("Missing Shotstack API key")

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
    if not SHOTSTACK_API_KEY:
        raise ValueError("Missing Shotstack API key")

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

async def upload_video(file: UploadFile = File(...)):
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        # Upload to Firebase
        firebase_url = await upload_to_firebase(file)
        print(f"firebase={firebase_url}")
        
        # Submit to Shotstack
        shotstack_response = await submit_to_shotstack(firebase_url)
        source_id = shotstack_response['data']['id']
        
        # Poll for status (with timeout)
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
        
        # If we get here, processing timed out
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
