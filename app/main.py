from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from video_generator import generate_video
from webhook_sender import send_webhook

app = FastAPI()

class VideoRequest(BaseModel):
    json_data: dict
    webhook_url: str

@app.post("/generate_video")
async def create_video(request: VideoRequest, background_tasks: BackgroundTasks):
    # Generate video in the background
    background_tasks.add_task(process_video_request, request)
    return {"message": "Video generation started"}

async def process_video_request(request: VideoRequest):
    # Generate the video
    video_path = generate_video(request.json_data)
    
    # Send the video via webhook
    send_webhook(request.webhook_url, video_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
