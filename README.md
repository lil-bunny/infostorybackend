Documentation: Text and Video Processing API
Overview
This API is designed for generating structured chart data and creating engaging videos from textual input. It leverages OpenAI's capabilities for natural language processing and integrates with Shotstack for video creation. This service is ideal for content creators and businesses looking to transform text into visually engaging multimedia.

Technology Stack
Backend Framework
FastAPI: A modern web framework for building APIs in Python. It's known for speed, simplicity, and easy integration with tools like Pydantic.
Key Libraries and Tools
OpenAI API: Used for generating insights and chart data from input text.
Pydantic: Provides data validation and settings management via Python typing.
Shotstack API: Handles video rendering and creation.
uvicorn: A lightning-fast ASGI server used to serve FastAPI applications.
Middleware:
CORS Middleware: Allows cross-origin requests, essential for frontend-backend integration.
JSON & AST Libraries: For handling and parsing JSON and Python-style structured data.
Endpoints
1. Generate Chart
Endpoint: /generate_chart/
Method: POST
Description: Generates a chart data structure in JSON format based on user-provided text.
Input:
json
Copy code
{
  "message": "Text describing a data trend or insights."
}
Output (HTML Response):
Returns a structured JSON in chart slide format.
Example Response:
json
Copy code
[
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
    "sub_text": "Are you ready?",
    "image_prompt": "An SVG infographic of a globe surrounded by icons representing Android and Apple users."
  }
]
2. Upload Video
Endpoint: /upload-video/
Method: POST
Description: Uploads a video file to the Shotstack platform.
Input: File (via multipart/form-data)
Output:
json
Copy code
{
  "success": true,
  "message": "Upload successful",
  "video_url": "https://cdn.shotstack.io/video.mp4",
  "source_id": "abc123"
}
3. Generate Video
Endpoint: /generate_video/
Method: POST
Description: Processes input text to create chart data and then generates a video using Shotstack.
Input:
json
Copy code
{
  "text": "Input text for video creation.",
  "video_url": "Optional video background URL"
}
Output:
Success Response:
json
Copy code
{
  "status": "success",
  "video_url": "https://cdn.shotstack.io/video.mp4"
}
Failure Response:
json
Copy code
{
  "status": "failed",
  "video_url": ""
}
Core Functionalities
1. Text Processing with OpenAI
Function: process_text_with_openai(text: str)
Description: Converts user input into structured data for chart creation.
Key Features:
Generates slide content based on structured storytelling.
Suggests visual elements (e.g., pie charts, infographics).
2. JSON/Array Parsing
Function: convert_to_array(input_data)
Description: Safely parses string inputs into Python list or JSON-compatible objects.
3. Shotstack Video Integration
Functions:

upload_video(file): Uploads a video file to Shotstack.
render_video_with_shotstack(api_key, clips_data, video_url): Creates a video using structured clip data.
check_render_status(api_key, render_id): Monitors video rendering progress.
Process Flow:

Generates clips based on structured chart data (loopThroughArray).
Sends clip data to Shotstack for rendering.
Returns the video URL upon completion.
4. ID Extraction
Function: extract_id_from_response(api_response)
Description: Extracts video render ID from Shotstack API responses for further processing.
Middleware Configuration
CORS: Ensures cross-origin resource sharing, allowing frontend applications to interact with the API securely.
python
Copy code
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Example Flow: Text to Video
Input: Submit text and optional video background URL to /generate_video/.
Processing:
Text is analyzed by OpenAI to create chart data.
Slide content is converted into video clips.
Clips are sent to Shotstack for rendering.
Output: Returns a video URL.
Error Handling
Input Validation:

Validates required fields using Pydantic.
Provides clear error messages for invalid input.
OpenAI Failures:

Catches API errors and returns descriptive messages.
Shotstack Failures:

Checks render status and retries or returns an error response.
Deployment
Server: uvicorn
Command:
bash
Copy code
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
This API transforms raw text into structured data, then creates high-quality videos seamlessly, making it a powerful tool for content creators and marketers.
