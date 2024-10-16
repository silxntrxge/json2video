import json
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import moviepy.video.fx.all as vfx
from moviepy.video.fx.resize import resize
import requests
from io import BytesIO
import numpy as np
import tempfile
import os
import imageio
import imageio.v3 as iio
import uuid
import imghdr
import cv2

def generate_video(json_data):
    try:
        video_spec = json_data
        video_clips = []
        audio_clips = []
        
        print("Starting video generation process...")
        print(f"Video specification: {json.dumps(video_spec, indent=2)}")
        
        # Set default values if not provided
        video_duration = video_spec.get('duration', 10.0)
        video_fps = video_spec.get('fps', 30)
        video_width = video_spec.get('width', 1280)
        video_height = video_spec.get('height', 720)
        
        for element in video_spec['elements']:
            if element['type'] == 'composition':
                for sub_element in element['elements']:
                    print(f"Processing composition element: {json.dumps(sub_element, indent=2)}")
                    clip = create_clip(sub_element, video_width, video_height, video_spec)
                    if clip:
                        if isinstance(clip, AudioFileClip):
                            audio_clips.append(clip)
                        else:
                            video_clips.append(clip)
                        print(f"Added clip from composition: {sub_element['id']}")
                    else:
                        print(f"Failed to create clip for composition element: {sub_element['id']}")
            else:
                print(f"Processing top-level element: {json.dumps(element, indent=2)}")
                clip = create_clip(element, video_width, video_height, video_spec)
                if clip:
                    if isinstance(clip, AudioFileClip):
                        audio_clips.append(clip)
                    else:
                        video_clips.append(clip)
                    print(f"Added top-level clip: {element['id']}")
                else:
                    print(f"Failed to create clip for top-level element: {element['id']}")
        
        print(f"Total video clips created: {len(video_clips)}")
        print(f"Total audio clips created: {len(audio_clips)}")
        
        if video_clips or audio_clips:
            # Remove clips with None start times or durations
            valid_video_clips = [clip for clip in video_clips if clip.start is not None and clip.duration is not None]
            valid_audio_clips = [clip for clip in audio_clips if clip.start is not None and clip.duration is not None]
            
            if len(valid_video_clips) != len(video_clips) or len(valid_audio_clips) != len(audio_clips):
                print(f"Warning: Removed {len(video_clips) - len(valid_video_clips)} video clips and {len(audio_clips) - len(valid_audio_clips)} audio clips with invalid start times or durations")
            
            # Sort clips based on track number and start time
            valid_video_clips.sort(key=lambda c: (getattr(c, 'track', 0), c.start))
            
            try:
                # Create the final composite clip
                final_clip = CompositeVideoClip(valid_video_clips, size=(video_width, video_height))
                
                # Ensure the final clip duration matches the specified duration
                final_clip = final_clip.set_duration(video_duration)
                
                # Add audio clips
                if valid_audio_clips:
                    final_audio = CompositeAudioClip(valid_audio_clips)
                    final_clip = final_clip.set_audio(final_audio)
                
                print(f"Final clip details:")
                print(f"  Duration: {final_clip.duration}")
                print(f"  Size: {final_clip.w}x{final_clip.h}")
                print(f"  FPS: {video_fps}")
                print(f"  Audio: {'Yes' if final_clip.audio else 'No'}")
                
                # Generate a unique filename for the output video
                unique_filename = f"output_video_{uuid.uuid4().hex}.mp4"
                desktop_path = os.path.expanduser("~/Desktop")
                output_path = os.path.join(desktop_path, unique_filename)
                
                print(f"Attempting to write video file to: {output_path}")
                
                final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=video_fps)
                
                if os.path.exists(output_path):
                    print(f"Video exported successfully to: {output_path}")
                    return output_path
                else:
                    print(f"Error: Video file was not created at {output_path}")
                    return None
            except Exception as e:
                print(f"Error creating or writing final clip: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
        else:
            print("Error: No valid clips were created")
            return None
    except Exception as e:
        print(f"Error generating video: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def download_font(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Create a temporary file to store the downloaded font
            with tempfile.NamedTemporaryFile(delete=False, suffix='.otf') as temp_font:
                temp_font.write(response.content)
                return temp_font.name
        else:
            print(f"Failed to download font from {url}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading font: {str(e)}")
        return None

def create_clip(element, video_width, video_height, video_spec):
    try:
        print(f"Starting to create clip for element: {element['id']}, type: {element['type']}")
        
        # Set default start_time and duration at the beginning
        start_time = element.get('time', 0.0)
        duration = element.get('duration')
        if duration is None:
            duration = video_spec.get('duration', 10.0) - start_time
            duration = max(duration, 0)  # Ensure duration is not negative

        print(f"Element details: start_time={start_time}, duration={duration}")

        source_url = element.get('source', '')
        print(f"Source URL: {source_url}")

        if source_url:
            try:
                is_gifv = source_url.lower().endswith('.gifv')
                print(f"Is GIFV: {is_gifv}")
            except AttributeError as e:
                print(f"Error checking if source is GIFV: {str(e)}")
                print(f"Source URL type: {type(source_url)}")
                is_gifv = False

        if element['type'] in ['image', 'video']:
            if element['source']:
                print(f"Downloading file from: {element['source']}")
                response = requests.get(element['source'])
                content_type = response.headers.get('content-type', '')
                
                if is_gifv or 'video' in content_type or element['type'] == 'video':
                    # Handle video or gifv as video
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                        temp_file.write(response.content)
                        temp_file_path = temp_file.name
                    clip = VideoFileClip(temp_file_path)
                    os.unlink(temp_file_path)
                    print(f"Video/Gifv clip created successfully: {element['id']}")
                elif 'image' in content_type or element['type'] == 'image':
                    # Handle static image or GIF
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.gif') as temp_file:
                        temp_file.write(response.content)
                        temp_file_path = temp_file.name

                    # Check if it's a GIF
                    if imghdr.what(temp_file_path) == 'gif':
                        # Handle GIF
                        gif = imageio.get_reader(temp_file_path)
                        frames = []
                        for frame in gif:
                            frames.append(frame)
                        
                        # Calculate fps based on GIF metadata
                        try:
                            fps_meta = gif.get_meta_data()
                            duration_ms = fps_meta.get('duration', 100)  # Duration per frame in ms
                            fps = 1000 / duration_ms if duration_ms > 0 else 10  # Default to 10 fps if duration is 0
                        except (KeyError, ZeroDivisionError):
                            fps = 10  # Default fps if metadata is not available
                        
                        clip = ImageSequenceClip(frames, fps=fps)
                        print(f"Animated GIF clip created successfully: {element['id']} with fps: {fps}")
                        
                        # Handle repeat for GIFs
                        if element.get('repeat', False):
                            clip = clip.loop(duration=duration)  # Loop the GIF
                            print(f"GIF '{element['id']}' will repeat for {duration} seconds.")
                    else:
                        # Handle static image
                        img = Image.open(temp_file_path)
                        if img.mode in ('P', 'PA'):
                            img = img.convert('RGBA')
                        elif img.mode not in ('RGB', 'RGBA'):
                            img = img.convert('RGB')
                        
                        img_array = np.array(img)
                        clip = ImageClip(img_array)
                        print(f"Static image clip created successfully: {element['id']}")
                    
                    os.unlink(temp_file_path)
                else:
                    print(f"Unsupported content type: {content_type}")
                    return None
                
                # Resize and position the clip
                clip = resize_and_position_clip(clip, element, video_width, video_height)
                
                # Set duration and handle repeat
                if duration is None:
                    duration = video_spec.get('duration', 10.0)  # Use the full video duration if not specified
                
                if element.get('repeat', False):
                    clip = clip.loop(duration=duration)  # Loop the clip if repeat is true
                else:
                    clip = clip.set_duration(duration)
                
                clip = clip.set_start(start_time)
                
                clip.name = element['id']
                clip.track = element.get('track', 0)
                
                return clip
            else:
                print(f"Skipping {element['type']} with empty source: {element['id']}")
                return None
        elif element['type'] == 'text':
            if element.get('text'):
                font_size = int(parse_size(element['font_size'], min(video_width, video_height)))
                font_path = element.get('font_family')
                print(f"Initial font_path: {font_path}")

                # Check if font_path is a URL and download if necessary
                if font_path:
                    try:
                        if isinstance(font_path, str) and font_path.lower().startswith('http'):
                            font_path = download_font(font_path)
                    except AttributeError as e:
                        print(f"Error processing font_path: {str(e)}")
                        font_path = None

                # Fallback to default font if download fails
                if not font_path:
                    font_path = "Arial"  # Fallback to default font
                    print(f"Using fallback font: Arial for element {element['id']}")
                else:
                    print(f"Using font: {font_path} for element {element['id']}")

                # Ensure text color is visible
                text_color = element.get('fill_color', 'white')

                # Log details for debugging
                print(f"Creating text clip for element: {element['id']}")
                print(f"  Text: {element['text']}")
                print(f"  Font size: {font_size}")
                print(f"  Font path: {font_path}")
                print(f"  Text color: {text_color}")
                print(f"  Position: ({element.get('x')}, {element.get('y')})")
                print(f"  Duration: {duration}")
                print(f"  Start time: {start_time}")

                # Create the text clip without setting size and align
                try:
                    text_clip = TextClip(
                        element['text'],
                        fontsize=font_size,
                        font=font_path,
                        color=text_color,
                        method='label',  # Changed from 'caption' to 'label'
                        transparent=True
                    )
                except Exception as e:
                    print(f"Error creating text clip for element {element['id']}: {str(e)}")
                    return None

                text_clip = text_clip.set_duration(duration)
                text_clip = resize_and_position_clip(text_clip, element, video_width, video_height)
                text_clip = text_clip.set_start(start_time)
                text_clip.name = element['id']
                text_clip.track = element.get('track', 0)
                return text_clip
            else:
                print(f"Skipping text with empty content: {element['id']}")
                return None
        elif element['type'] == 'audio':
            if element['source']:
                audio_clip = AudioFileClip(element['source'])
                if duration is not None:
                    audio_clip = audio_clip.subclip(0, duration)
                volume = element.get('volume')
                if volume is not None:
                    try:
                        volume_value = float(volume.rstrip('%')) / 100
                        audio_clip = audio_clip.volumex(volume_value)
                    except ValueError:
                        print(f"Invalid volume value for audio element: {element['id']}, using default volume.")
                audio_clip = audio_clip.set_start(start_time)
                audio_clip.name = element['id']
                audio_clip.track = element.get('track', 0)
                return audio_clip
            else:
                print(f"Skipping audio with empty source: {element['id']}")
                return None
        else:
            print(f"Unknown element type: {element['type']}")
            return None
    except Exception as e:
        print(f"Error creating clip for element: {element}")
        print(f"Error details: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def resize_and_position_clip(clip, element, video_width, video_height):
    print(f"Resizing and positioning clip for element: {element['id']}")
    print(f"Original clip size: {clip.w}x{clip.h}")
    print(f"Video size: {video_width}x{video_height}")

    # Parse width and height
    element_width = parse_size(element.get('width'), video_width)
    element_height = parse_size(element.get('height'), video_height)
    print(f"Parsed width: {element_width}, Parsed height: {element_height}")

    # Determine fit mode
    fit_mode = element.get('fit', 'cover').lower()
    print(f"Fit mode for element '{element['id']}': {fit_mode}")

    if element['type'] != 'text':
        if element_width and element_height:
            if fit_mode == 'cover':
                # Scale the clip to cover the specified width and height, cropping if necessary
                clip = clip.resize(lambda t: max(element_width / clip.w, element_height / clip.h))
                print(f"[Cover] Resized clip size: {clip.w}x{clip.h}")
            elif fit_mode == 'contain':
                # Scale the clip to fit within the specified width and height, maintaining aspect ratio
                clip = clip.resize(lambda t: min(element_width / clip.w, element_height / clip.h))
                print(f"[Contain] Resized clip size: {clip.w}x{clip.h}")
            elif fit_mode == 'fill':
                # Stretch the clip to exactly fit the specified width and height, possibly distorting aspect ratio
                clip = clip.resize(width=element_width, height=element_height)
                print(f"[Fill] Resized clip size: {clip.w}x{clip.h}")
            else:
                print(f"Unknown fit mode '{fit_mode}' for element {element['id']}, using 'cover' as default.")
                clip = clip.resize(lambda t: max(element_width / clip.w, element_height / clip.h))
                print(f"[Default Cover] Resized clip size: {clip.w}x{clip.h}")
    else:
        print("Skipping resizing for text element")
        # Text elements maintain their natural size based on font_size

    # Parse x and y positions
    x = parse_size(element.get('x'), video_width)
    y = parse_size(element.get('y'), video_height)
    print(f"Parsed position - x: {x}, y: {y}")

    if element['type'] == 'text':
        # Parse anchor points for text
        x_anchor = parse_size(element.get('x_anchor', '50%'), clip.w)
        y_anchor = parse_size(element.get('y_anchor', '50%'), clip.h)
        
        print(f"Text Element - x_anchor: {x_anchor}, y_anchor: {y_anchor}")

        # Calculate position based on anchor points
        if x is not None and x_anchor is not None:
            x = int(x - x_anchor)
        else:
            x = (video_width - clip.w) // 2  # Center horizontally if x or anchor missing

        if y is not None and y_anchor is not None:
            y = int(y - y_anchor)
        else:
            y = (video_height - clip.h) // 2  # Center vertically if y or anchor missing
    else:
        # For images/gifs/videos, use x and y as top-left positions without anchors
        print("Positioning image/gif/video element based on top-left coordinates")
        if x is None:
            x = (video_width - clip.w) // 2  # Center horizontally if x not provided
            print(f"x not provided. Centering horizontally: {x}")
        if y is None:
            y = (video_height - clip.h) // 2  # Center vertically if y not provided
            print(f"y not provided. Centering vertically: {y}")

    print(f"Calculated position before clamping - x: {x}, y: {y}")

    # Ensure position is within bounds
    x = max(0, min(x, video_width - clip.w))
    y = max(0, min(y, video_height - clip.h))

    print(f"Final position after clamping - x: {x}, y: {y}")

    # Set position
    clip = clip.set_position((x, y))

    return clip

def parse_size(size_str, reference_size):
    print(f"Parsing size: '{size_str}' with reference size: {reference_size}")
    if size_str is None:
        print("Size string is None.")
        return None
    if isinstance(size_str, (int, float)):
        size = int(size_str)
        size = max(0, min(size, reference_size))  # Clamp between 0 and reference_size
        print(f"Size is a number: {size}")
        return size
    if isinstance(size_str, str):
        size_str = size_str.strip()
        if size_str.endswith('%'):
            try:
                percentage = float(size_str[:-1])
                percentage = max(0, min(percentage, 100))  # Clamp between 0% and 100%
                parsed_size = int(percentage * reference_size / 100)
                print(f"Parsed percentage size: {parsed_size} (from {percentage}%)")
                return parsed_size
            except ValueError:
                print(f"Invalid size percentage: {size_str}")
                return None
        elif size_str.endswith('vmin'):
            try:
                vmin_value = float(size_str[:-4])
                vmin = min(reference_size, reference_size)  # Typically, 'vmin' is based on the smaller dimension
                vmin_value = max(0, min(vmin_value, 100))  # Clamp between 0 and 100
                parsed_size = int(vmin_value * vmin / 100)
                print(f"Parsed vmin size: {parsed_size} (from {vmin_value} vmin)")
                return parsed_size
            except ValueError:
                print(f"Invalid size vmin: {size_str}")
                return None
        else:
            try:
                parsed_size = int(float(size_str))
                parsed_size = max(0, min(parsed_size, reference_size))  # Clamp between 0 and reference_size
                print(f"Parsed absolute size: {parsed_size}")
                return parsed_size
            except ValueError:
                print(f"Invalid size format: {size_str}")
                return None
    print("Size string format not recognized.")
    return None

# Update the resize function to use the current recommended resampling filter
def updated_resize(clip, newsize=None, height=None, width=None, apply_to_mask=True):
    if hasattr(Image, 'ANTIALIAS'):
        resample = Image.ANTIALIAS
    else:
        resample = Image.LANCZOS
    
    def resize_image(img):
        return img.resize(newsize[::-1], resample)
    
    return clip.image_transform(resize_image)

# Monkey-patch moviepy's resize function
vfx.resize = updated_resize
resize.resize = updated_resize

# Patch PIL.Image.ANTIALIAS if not present
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

def render_text_on_video(video_path, text, position, font, color):
    # Ensure the video file is loaded correctly
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print("Error: Could not open video.")
        return

    # Check if the font is loaded correctly
    if not font:
        print("Error: Font not loaded.")
        return

    print(f"Rendering text: '{text}' at position: {position} with color: {color}")

    # Loop through video frames
    frame_count = 0
    while True:
        ret, frame = video.read()
        if not ret:
            print("No more frames to read or error reading frame.")
            break

        # Render text on the frame
        cv2.putText(frame, text, position, font, 1, color, 2, cv2.LINE_AA)

        # Display the frame (for debugging)
        cv2.imshow('Video', frame)
        frame_count += 1
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print(f"Total frames processed: {frame_count}")
    video.release()
    cv2.destroyAllWindows()
