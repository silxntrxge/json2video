from fastapi import FastAPI, BackgroundTasks, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Union
from .video_generator import generate_video
from .webhook_sender import send_webhook
import logging
import os
import sys

# Add these lines at the beginning for debugging
print("Python version:", sys.version)
print("Current working directory:", os.getcwd())
print("Contents of current directory:", os.listdir())

app = FastAPI()

class Animation(BaseModel):
    easing: str
    type: str
    fade: bool
    scope: str
    end_scale: str
    start_scale: str

class SubElement(BaseModel):
    id: str
    type: str
    name: Optional[str] = None
    track: Optional[int] = None
    time: Optional[float] = None
    duration: Optional[float] = None
    source: Optional[str] = None
    x: Optional[str] = None
    y: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None
    x_anchor: Optional[str] = None
    y_anchor: Optional[str] = None
    fill_color: Optional[str] = None
    text: Optional[str] = None
    font_family: Optional[str] = None
    font_size: Optional[str] = None

class Element(SubElement):
    elements: Optional[List[SubElement]] = None

class VideoRequest(BaseModel):
    output_format: str
    width: int
    height: int
    duration: float
    snapshot_time: Optional[float] = None  # Make this optional
    elements: List[Union[SubElement, Element]]  # Allow both SubElement and Element

@app.post("/generate_video")
async def create_video(request: VideoRequest, background_tasks: BackgroundTasks, x_webhook_url: str = Header(...)):
    # Generate video in the background
    background_tasks.add_task(process_video_request, request.dict(), x_webhook_url)
    return {"message": "Video generation started"}

async def process_video_request(json_data: dict, webhook_url: str):
    # Generate the video and get the upload URL
    video_url = generate_video(json_data)
    
    if video_url:
        try:
            # Send the video URL via webhook
            send_webhook(webhook_url, video_url)
            logging.info(f"Sent webhook with video URL: {video_url}")
        except Exception as e:
            logging.error(f"Error sending webhook: {str(e)}")
    else:
        logging.error("Video generation failed; webhook not sent.")

@app.get("/")
async def root():
    return {"message": "JSON2Video API is running"}

@app.post("/generate")
async def generate_video_endpoint(data: dict):
    # Your video generation logic here
    # Use generate_video function from video_generator.py
    # Use send_webhook function from webhook_sender.py
    pass
