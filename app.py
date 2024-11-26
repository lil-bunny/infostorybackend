import ast
import json
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional
from openai import OpenAI
import os
import uvicorn
from generatechart import chat 
from fastapi.middleware.cors import CORSMiddleware

from shotstackupload import upload_video
from videocreationhelper import render_video_with_shotstack, check_render_status,loopThroughArray
# Load environment variables


# Initialize FastAPI app
app = FastAPI(
    
    title="Text Processing API",
    description="API for processing text and video URLs using OpenAI",
    version="1.0.0",

)
app.add_middleware(  CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  )

# Initialize OpenAI client
client = OpenAI(api_key='')

# Request models
class TextRequest(BaseModel):
    text: str
    video_url: Optional[HttpUrl] = None

# Response models
class ProcessedResponse(BaseModel):
    processed_text: str
    chart_data: Optional[list] = None
    error: Optional[str] = None

def process_text_with_openai(text: str) -> str:
    try:
        # Construct the prompt for chart conversion
        # prompt = f"""
        # Analyze the following text and convert it into a suitable chart format if possible.
        # If the text contains numerical data or trends, suggest an appropriate chart type.
        
        # Text: {text}
        
        # Please provide:
        # 1. Whether this text can be converted to a chart
        # 2. If yes, what type of chart would be most suitable
        # 3. The structured data format for the chart
        # """
        prompt="""
Act as a social media content creator specialised in analytics or understanding data 
i will input a sentence that could be converted to charts.
you give me a script of informative script story telling the data  .There must be 5 slides.
Follow below Reference for the response structure:
"""+f"""{[
    {
      "slide_number": 1,
      "purpose": "Heading of Topic",
      "main_text": "Android vs Apple",
      "sub_text": "Which smartphone OS dominates the market?",
      "image_prompt": "An SVG illustration of two smartphones side-by-side, one with the Android logo and the other with the Apple logo."
    },
    {
      "slide_number": 2,
      "purpose": "Topic Setup",
      "main_text": "Ever wondered which operating system people prefer? Let’s break it down!",
      'sub_text':"Aret you ready?",
      "image_prompt": "An SVG infographic of a globe surrounded by icons representing Android and Apple users."
    },
    {
      "slide_number": 3,
      "purpose": "Data Highlight",
      "main_text": "The numbers are clear:",
      "sub_text": "90% of users are on Android, while 10% stick with Apple.",
      "pie_chart": {
        "Android": 90,
        "Apple": 10
      }
    },
    {
      "slide_number": 4,
      "purpose": "Short Insight from Data",
      "main_text": "What does this mean?",
      "sub_text": "Android dominates due to affordability and variety, while Apple retains a premium niche.",
      "image_prompt": "A futuristic AI-generated scene of a busy street with people holding a variety of smartphones, showcasing diversity in Android devices and a smaller group holding sleek Apple phones."
    },
    {
      "slide_number": 5,
      "purpose": "Conclusion",
      "main_text": "The choice is yours!",
      "sub_text": "Whether it’s Android’s flexibility or Apple’s exclusivity, both have their strengths.",
      "image_prompt": "A side-by-side comparison of a glowing Android logo and a polished Apple logo, glowing in a dark backdrop."
    }
  ]   }"""+""".\nGIve response in JSON format like above totally,and dont make mistake .and dont use extra words in the response.i Just want structured response"""
        userprompt=f"input={text}"
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "user", "content": prompt},
                {"role": "user", "content":userprompt }
            ],
            temperature=0.2
        )
        
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
def convert_to_array(input_data):
    """
    Convert any JSON-like string or Python object into a Python list of dictionaries.

    Args:
        input_data (str or object): The input data to be converted. It can be:
            - A string (JSON or Python-style list)
            - An already parsed Python object

    Returns:
        list: A list of dictionaries if the input is valid; otherwise, None.
    """
    try:
        # If input is already a Python object, return if it's a list
        if isinstance(input_data, list):
            return input_data

        # If the input is a string, attempt to parse it
        if isinstance(input_data, str):
            # Try parsing as JSON
            try:
                return json.loads(input_data)
            except json.JSONDecodeError:
                pass  # Fall back to `ast.literal_eval` for Python-style strings
            
            # Try parsing as a Python literal (e.g., single quotes, etc.)
            try:
                return ast.literal_eval(input_data)
            except (ValueError, SyntaxError):
                pass

        # If none of the above worked, return an error
        raise ValueError("Input could not be parsed into a list of dictionaries.")
    
    except Exception as e:
        print(f"Error during conversion: {e}")
        return None
class ChatRequest(BaseModel):
    message: str
class UploadResponse(BaseModel):
    success: bool
    message: str
    video_url: Optional[str] = None
    source_id: Optional[str] = None
def extract_id_from_response(api_response):
    """
    Extract the 'id' from the API response if it exists and the response is structured correctly.
    
    Args:
        api_response (dict): The response dictionary from the API.
        
    Returns:
        str: The extracted 'id' if present, otherwise None.
    """
    try:
        # Check if 'success' is True and 'response' contains an 'id'
        if (
            isinstance(api_response, dict) 
            and api_response.get('success') is True 
            and 'response' in api_response 
            and 'id' in api_response['response']
        ):
            return api_response['response']['id']
        else:
            print("Invalid response format or missing 'id'.")
            return None
    except Exception as e:
        print(f"Error while extracting 'id': {e}")
        return None
@app.post("/generate_chart/",response_class=HTMLResponse)
async def generate_chart(request:ChatRequest):
    return await chat(request=request)

@app.post("/upload-video/", response_model=UploadResponse)
async def upload_shotstack(file: UploadFile = File(...)):
    return await upload_video(file=file)


# response_model=ProcessedResponse
@app.post("/generate_video/", )
async def process_text(request: TextRequest):
    try:
        # Process the text using OpenAI
        processed_result = process_text_with_openai(request.text)
        
        # Create the response
        response = ProcessedResponse(
            processed_text=request.text,
            chart_data=convert_to_array(processed_result)
        )
        
        clips_data=loopThroughArray(response.chart_data,videourl=request.video_url)
        renderresponse=render_video_with_shotstack(api_key='epz8h0zzhH9mtbIHAlFSNmexHP66CXAI4bwECcur',clips_data=clips_data,videourl=request.
        video_url)
        renderedid=extract_id_from_response(renderresponse)
        try:
            if(renderedid !=None):
                return check_render_status(api_key='epz8h0zzhH9mtbIHAlFSNmexHP66CXAI4bwECcur',render_id=renderedid)        
        except Exception as e:
            return {
                "status":"failed",
                "video_url":""}

            
        return  {
            "status":"failed",
            "video_url":""}

    except Exception as e:
        # return ProcessedResponse(
        #     processed_text=request.text,
        #     error=str(e)
        # )
        return  {
            "status":"failed",
            "video_url":""}        
