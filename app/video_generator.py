import json
from moviepy.editor import *
from PIL import Image
import moviepy.video.fx.all as vfx
from moviepy.video.fx.resize import resize

def generate_video(json_data):
    try:
        # Parse the JSON data
        video_spec = json_data
        
        # Create a list to store all the clips
        clips = []
        
        # Process each element in the JSON
        for element in video_spec['elements']:
            if element['type'] == 'composition':
                for sub_element in element['elements']:
                    clip = create_clip(sub_element, video_spec['width'], video_spec['height'])
                    if clip:
                        clips.append(clip)
        
        # Combine all clips
        final_clip = CompositeVideoClip(clips, size=(video_spec['width'], video_spec['height']))
        final_clip = final_clip.set_duration(video_spec['duration'])
        
        # Set a default fps if not provided in the JSON
        fps = video_spec.get('fps', 30)
        
        # Write the final video file
        output_path = "/tmp/output_video.mp4"
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=fps)
        
        return output_path
    except Exception as e:
        print(f"Error generating video: {str(e)}")
        raise

def create_clip(element, video_width, video_height):
    try:
        if element['type'] == 'image':
            clip = ImageClip(element['source']).set_duration(element['duration'])
            clip = set_position(clip, element, video_width, video_height)
            if 'animations' in element:
                for animation in element['animations']:
                    if animation['type'] == 'scale':
                        clip = clip.resize(lambda t: 1 + (float(animation['end_scale'][:-1]) - 100) / 100 * t / clip.duration)
            return clip
        elif element['type'] == 'video':
            clip = VideoFileClip(element['source'])
            clip = set_position(clip, element, video_width, video_height)
            return clip
        elif element['type'] == 'text':
            font_size = parse_size(element['font_size'], min(video_width, video_height))
            clip = TextClip(element['text'], fontsize=font_size, color=element['fill_color'], font=element.get('font_family', 'Arial'))
            clip = set_position(clip, element, video_width, video_height)
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

def set_position(clip, element, video_width, video_height):
    x = parse_size(element.get('x', '0%'), video_width)
    y = parse_size(element.get('y', '0%'), video_height)
    
    # Handle alignment
    x_alignment = element.get('x_alignment', '0%')
    y_alignment = element.get('y_alignment', '0%')
    
    if x_alignment == '50%':
        x -= clip.w / 2
    elif x_alignment == '100%':
        x -= clip.w
    
    if y_alignment == '50%':
        y -= clip.h / 2
    elif y_alignment == '100%':
        y -= clip.h
    
    return clip.set_position((x, y))

def parse_size(size_str, reference_size):
    if isinstance(size_str, (int, float)):
        return size_str
    if size_str.endswith('%'):
        return float(size_str[:-1]) * reference_size / 100
    if size_str.endswith('vmin'):
        return float(size_str[:-4]) * min(video_width, video_height) / 100
    return float(size_str)

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
