import requests

def send_webhook(webhook_url, video_path):
    with open(video_path, 'rb') as video_file:
        files = {'video': video_file}
        response = requests.post(webhook_url, files=files)
    
    if response.status_code == 200:
        print(f"Video sent successfully to {webhook_url}")
    else:
        print(f"Failed to send video to {webhook_url}. Status code: {response.status_code}")
