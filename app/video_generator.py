import json
from moviepy.editor import *
from PIL import Image
import moviepy.video.fx.all as vfx
from moviepy.video.fx.resize import resize

def generate_video(json_data):
    # Parse the JSON data
    video_spec = json_data
    
    # Create a list to store all the clips
    clips = []
    
    # Process each element in the JSON
    for element in video_spec['elements']:
        if element['type'] == 'composition':
            for sub_element in element['elements']:
                clip = create_clip(sub_element)
                if clip:
                    clips.append(clip)
    
    # Combine all clips
    final_clip = CompositeVideoClip(clips, size=(video_spec['width'], video_spec['height']))
    final_clip = final_clip.set_duration(video_spec['duration'])
    
    # Write the final video file
    output_path = "/tmp/output_video.mp4"
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    
    return output_path

def create_clip(element):
    try:
        if element['type'] == 'image':
            clip = ImageClip(element['source']).set_duration(element['duration'])
            clip = clip.set_position((element.get('x', 0), element.get('y', 0)))
            if 'animations' in element:
                for animation in element['animations']:
                    if animation['type'] == 'scale':
                        clip = clip.resize(lambda t: 1 + (float(animation['end_scale'][:-1]) - 100) / 100 * t / clip.duration)
            return clip
        elif element['type'] == 'video':
            clip = VideoFileClip(element['source'])
            clip = clip.set_position((element.get('x', 0), element.get('y', 0)))
            return clip
        elif element['type'] == 'text':
            # Convert font_size to integer
            font_size = int(element['font_size'].split()[0])  # Assuming font_size is like "6 vmin"
            clip = TextClip(element['text'], fontsize=font_size, color=element['fill_color'], font=element['font_family'])
            clip = clip.set_position((element.get('x', 0), element.get('y', 0)))
            return clip
        elif element['type'] == 'audio':
            return AudioFileClip(element['source'])
        else:
            print(f"Unknown element type: {element['type']}")
            return None
    except Exception as e:
        print(f"Error creating clip for element: {element}")
        print(f"Error details: {str(e)}")
        return None

# Update the resize function to use the current recommended resampling filter
def updated_resize(clip, newsize=None, height=None, width=None, apply_to_mask=True):
    if Image.ANTIALIAS:
        resample = Image.ANTIALIAS
    else:
        resample = Image.LANCZOS
    
    def resize_image(img):
        return img.resize(newsize[::-1], resample)
    
    return clip.image_transform(resize_image)

# Monkey-patch moviepy's resize function
vfx.resize = updated_resize
resize.resize = updated_resize

# Patch PIL.Image.ANTIALIAS
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
