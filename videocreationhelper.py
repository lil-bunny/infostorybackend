import json
import time
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Configuration
SHOTSTACK_API_KEY = os.getenv('SHOTSTACK_API_KEY')
SHOTSTACK_EDIT_API_URL = os.getenv('SHOTSTACK_EDIT_API_URL', 'https://api.shotstack.io/edit/stage')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Validate required environment variables
if not SHOTSTACK_API_KEY:
    raise ValueError("Missing SHOTSTACK_API_KEY environment variable")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable")

def createImageAndVideo(maintext: str, subtext: str, videourl: str, start: int) -> List[Dict[str, Any]]:
    trackData = [   
        {
            "clips": [
                {
                    "asset": {
                        "type": "text",
                        "text": f"{subtext}",
                        "alignment": {
                            "horizontal": "center",
                            "vertical": "center"
                        },
                        "font": {
                            "color": "#000000",
                            "family": "Montserrat SemiBold",
                            "size": 24,
                            "lineHeight": 1
                        },
                        "width": 541,
                        "height": 72,
                        "background": {
                            "color": "#ffffff",
                            "borderRadius": 20
                        }
                    },
                    "start": start,
                    "length": 3,
                    "offset": {
                        "x": 0.008,
                        "y": -0.367
                    },
                    "position": "center",
                    "transition": {
                        "in": "carouselRight",
                        "out": "carouselRight"
                    }
                }
            ]
        },
        {
            "clips": [
                {
                    "asset": {
                        "type": "text",
                        "text": f"{maintext}",
                        "alignment": {
                            "horizontal": "center",
                            "vertical": "center"
                        },
                        "font": {
                            "color": "#000000",
                            "family": "Montserrat ExtraBold",
                            "size": 26,
                            "lineHeight": 1
                        },
                        "width": 688,
                        "height": 100,
                        "background": {
                            "color": "#ffffff",
                            "borderRadius": 39
                        }
                    },
                    "start": start,
                    "length": 3,
                    "offset": {
                        "x": 0,
                        "y": -0.284
                    },
                    "position": "center",
                    "transition": {
                        "out": "zoom",
                        "in": "zoom"
                    }
                }
            ]
        },
        {
            "clips": [
                {
                    "length": 3,
                    "asset": {
                        "type": "video",
                        "src": f"{videourl}",
                        "volume": 1
                    },
                    "start": start,
                    "offset": {
                        "x": 0,
                        "y": 0.029
                    },
                    "position": "center",
                    "scale": 0.300,
                    "transition": {
                        "in": "slideRight",
                        "out": "carouselUp"
                    }
                }
            ]
        }
    ]
    return trackData

def createImageAndText(maintext: str, subtext: str, imagetext: str, start: int) -> List[Dict[str, Any]]:
    trackData = [
        {
            "clips": [
                {
                    "asset": {
                        "type": "text",
                        "text": f"{subtext}",
                        "alignment": {
                            "horizontal": "center",
                            "vertical": "center"
                        },
                        "font": {
                            "color": "#000000",
                            "family": "Montserrat SemiBold",
                            "size": 24,
                            "lineHeight": 1
                        },
                        "width": 541,
                        "height": 72,
                        "background": {
                            "color": "#ffffff",
                            "borderRadius": 20
                        }
                    },
                    "start": start,
                    "length": 3,
                    "offset": {
                        "x": 0.008,
                        "y": -0.367
                    },
                    "position": "center",
                    "transition": {
                        "in": "carouselRight",
                        "out": "carouselRight"
                    }
                }
            ]
        },
        {
            "clips": [
                {
                    "asset": {
                        "type": "text",
                        "text": f"{maintext}",
                        "alignment": {
                            "horizontal": "center",
                            "vertical": "center"
                        },
                        "font": {
                            "color": "#000000",
                            "family": "Montserrat ExtraBold",
                            "size": 26,
                            "lineHeight": 1
                        },
                        "width": 688,
                        "height": 100,
                        "background": {
                            "color": "#ffffff",
                            "borderRadius": 39
                        }
                    },
                    "start": start,
                    "length": 3,
                    "offset": {
                        "x": 0,
                        "y": -0.284
                    },
                    "position": "center",
                    "transition": {
                        "out": "zoom",
                        "in": "zoom"
                    }
                }
            ]
        },
        {
            "clips": [
                {
                    "length": 3,
                    "asset": {
                        "type": "text-to-image",
                        "prompt": f"{imagetext}"
                    },
                    "start": start,
                    "effect": "slideLeftSlow",
                    "offset": {
                        "x": 0.03,
                        "y": 0
                    },
                    "position": "center",
                    "transition": {
                        "out": "zoom"
                    }
                }
            ]
        }
    ]
    
    if not subtext:
        trackData.pop(0)
    return trackData

def generateVideoTracks(index: int, maintext: str, subtext: str, image: str, start: int) -> List[Dict[str, Any]]:
    if index == 2:
        return createImageAndVideo(subtext=subtext, maintext=maintext, videourl=image, start=start)
    else:
        return createImageAndText(imagetext=image, maintext=maintext, subtext=subtext, start=start)

def merge_inner_elements(array: List[List[Any]]) -> List[Any]:
    """Merges all the inner elements from subarrays into a single array."""
    return [element for subarray in array for element in subarray]

def loopThroughArray(data: List[Dict[str, Any]], videourl: str) -> List[Dict[str, Any]]:
    fulltrack = []
    start = 0
    for item in data:
        index = item.get('slide_number')
        maintext = item.get('main_text', '')
        subtext = item.get('sub_text', '')
        image = item.get('image_prompt', item.get('image', ''))
        
        if index == 3:
            image = videourl
            
        track = generateVideoTracks(
            index=index-1,
            maintext=maintext,
            subtext=subtext,
            image=image,
            start=start
        )
        fulltrack.append(track)
        start += 3
        
    return merge_inner_elements(fulltrack)

async def render_video_with_shotstack(clips_data: List[Dict[str, Any]], videourl: str) -> Dict[str, Any]:
    """Sends a POST request to the Shotstack API to render a video."""
    url = f"{SHOTSTACK_EDIT_API_URL}/render"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": SHOTSTACK_API_KEY
    }

    payload = {
        "timeline": {
            "background": "#fcff33",
            "tracks": clips_data
        },
        "output": {
            "format": "mp4",
            "fps": 25,
            "size": {
                "width": 720,
                "height": 1280
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Shotstack API error: {str(e)}")

async def check_render_status(render_id: str) -> Dict[str, str]:
    """Polls the Shotstack API to check the render status of a video."""
    url = f"{SHOTSTACK_EDIT_API_URL}/render/{render_id}"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": SHOTSTACK_API_KEY
    }

    try:
        while True:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            status = data.get('response', {}).get('status')

            if status == 'done':
                video_url = data.get('response', {}).get('url')
                return {
                    "status": "done",
                    "video_url": video_url
                }
            elif status == 'failed':
                return {
                    "status": "failed",
                    "video_url": ""
                }
            
            await asyncio.sleep(10)  # Non-blocking sleep

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

# FastAPI Models
class ChartRequest(BaseModel):
    text: str
    video_url: str

class ChartResponse(BaseModel):
    render_id: str
    status: str
    video_url: Optional[str] = None

# FastAPI App
app = FastAPI()

@app.post("/generate-video", response_model=ChartResponse)
async def generate_video(request: ChartRequest):
    try:
        # Generate presentation data using OpenAI
        messages = [
            {"role": "user", "content": request.text}
        ]
        
        response = openai.ChatCompletion.create(
            model="gpt-4-mini",
            messages=messages,
            temperature=0.2
        )
        
        presentation_data = json.loads(response.choices[0].message.content)
        
        # Generate video clips
        clips_data = loopThroughArray(presentation_data, request.video_url)
        
        # Render video
        render_response = await render_video_with_shotstack(clips_data, request.video_url)
        render_id = render_response.get('response', {}).get('id')
        
        if not render_id:
            raise HTTPException(status_code=500, detail="Failed to get render ID from Shotstack")
            
        # Check initial status
        status_response = await check_render_status(render_id)
        
        return ChartResponse(
            render_id=render_id,
            status=status_response["status"],
            video_url=status_response.get("video_url")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/render-status/{render_id}", response_model=ChartResponse)
async def get_render_status(render_id: str):
    try:
        status_response = await check_render_status(render_id)
        return ChartResponse(
            render_id=render_id,
            status=status_response["status"],
            video_url=status_response.get("video_url")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
