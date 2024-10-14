import json
from moviepy.editor import *

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
        clip = TextClip(element['text'], fontsize=element['font_size'], color=element['fill_color'], font=element['font_family'])
        clip = clip.set_position((element.get('x', 0), element.get('y', 0)))
        return clip
    elif element['type'] == 'audio':
        return AudioFileClip(element['source'])
    return None
