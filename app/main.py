from fastapi import FastAPI, BackgroundTasks, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Union
from video_generator import generate_video
from webhook_sender import send_webhook
import logging
import os
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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
    snapshot_time: Optional[float] = None
    elements: List[Union[SubElement, Element]]

@app.post("/generate_video")
async def create_video(request: VideoRequest, background_tasks: BackgroundTasks, x_webhook_url: str = Header(...)):
    logging.info("Received video generation request")
    background_tasks.add_task(process_video_request, request.dict(), x_webhook_url)
    return {"message": "Video generation started"}

async def process_video_request(json_data: dict, webhook_url: str):
    logging.info("Starting video generation process")
    video_url = generate_video(json_data)
    
    if video_url:
        try:
            logging.info(f"Video generated successfully. URL: {video_url}")
            send_webhook(webhook_url, video_url)
            logging.info("Webhook sent successfully")
        except Exception as e:
            logging.error(f"Error sending webhook: {str(e)}")
    else:
        logging.error("Video generation failed; webhook not sent.")

@app.get("/")
async def root():
    return {"message": "JSON2Video API is running"}

if __name__ == "__main__":
    # Check if running in a production environment
    if os.environ.get("ENV") == "production":
        # Production settings
        host = "0.0.0.0"
        port = int(os.environ.get("PORT", 8000))
    else:
        # Local development settings
        host = "127.0.0.1"
        port = 8000

    # Run the server
    uvicorn.run(app, host=host, port=port)
