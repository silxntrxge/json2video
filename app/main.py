from fastapi import FastAPI, BackgroundTasks, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Union
from .video_generator import generate_video
from .webhook_sender import send_webhook
import logging
import os
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from concurrent.futures import ProcessPoolExecutor

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

# Create a ProcessPoolExecutor with a maximum of 2 workers
process_pool = ProcessPoolExecutor(max_workers=2)

@app.post("/generate_video")
async def create_video(request: VideoRequest, background_tasks: BackgroundTasks, x_webhook_url: str = Header(...)):
    logging.info("Received video generation request")
    background_tasks.add_task(process_video_request_with_timeout, request.dict(), x_webhook_url)
    return {"message": "Video generation started"}

async def process_video_request_with_timeout(json_data: dict, webhook_url: str):
    try:
        # Use ProcessPoolExecutor to run the CPU-intensive task
        loop = asyncio.get_event_loop()
        video_url = await loop.run_in_executor(process_pool, generate_video, json_data)
        
        if video_url:
            logging.info(f"Video generated successfully. URL: {video_url}")
            retry_count = 3
            while retry_count > 0:
                try:
                    send_webhook(webhook_url, video_url)
                    logging.info("Webhook sent successfully")
                    break
                except Exception as e:
                    logging.error(f"Error sending webhook (attempt {4-retry_count}/3): {str(e)}")
                    retry_count -= 1
                    if retry_count == 0:
                        logging.error("Failed to send webhook after 3 attempts")
        else:
            logging.error("Video generation failed; webhook not sent.")
    except asyncio.TimeoutError:
        logging.error("Video generation timed out")
        send_webhook(webhook_url, {"error": "Video generation timed out"})
    except Exception as e:
        logging.error(f"Error in video generation process: {str(e)}")
        send_webhook(webhook_url, {"error": str(e)})

@app.get("/")
async def root():
    return {"message": "JSON2Video API is running"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
