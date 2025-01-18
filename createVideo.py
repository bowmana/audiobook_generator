from moviepy.editor import AudioFileClip, ImageClip, TextClip, CompositeVideoClip, ColorClip
import os
from PIL import Image
from moviepy.config import change_settings
from openai import OpenAI, OpenAIError, RateLimitError, APIConnectionError
from dotenv import load_dotenv
from openaihelpers import retry_on_rate_limit

# Load environment variables and set up OpenAI
load_dotenv()
client = OpenAI(api_key=os.getenv("SECRET_KEY"))
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe"})
def transcribe_audio(audio_file):
    """Transcribe audio file using OpenAI's Whisper model"""
    print("Transcribing audio...")
    
    def _do_transcription(file_path):
        with open(file_path, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                file=audio,
                model="whisper-1",
                response_format="srt"
            )
        return transcript

    # Audio transcription typically uses about 1 token per second of audio
    audio_duration = AudioFileClip(audio_file).duration
    estimated_tokens = int(audio_duration)
    
    result = retry_on_rate_limit(_do_transcription, audio_file, estimated_tokens=estimated_tokens)
    if result is None:
        print("Failed to transcribe audio after multiple retries")
        return None
    return result

def parse_srt(srt_content):
    """Parse SRT format into list of (start_time, end_time, text, context) tuples"""
    segments = []
    lines = srt_content.strip().split('\n\n')
    
    # Build complete text first
    all_sentences = []
    for line in lines:
        parts = line.split('\n')
        if len(parts) >= 3:
            text = ' '.join(parts[2:])
            all_sentences.append(text)
    
    # Create segments with lookahead context
    for i, line in enumerate(lines):
        parts = line.split('\n')
        if len(parts) >= 3:
            times = parts[1].split(' --> ')
            start_time = convert_timestamp_to_seconds(times[0])
            end_time = convert_timestamp_to_seconds(times[1])
            current_sentence = ' '.join(parts[2:])
            
            # Get next 5-10 sentences as context (or remaining sentences if less)
            context_end = min(i + 10, len(all_sentences))
            context = '\n\n'.join(all_sentences[i:context_end])
            
            segments.append((
                start_time,
                end_time,
                current_sentence,  # Active sentence
                context  # Next several sentences
            ))
    
    return segments

def convert_timestamp_to_seconds(timestamp):
    """Convert SRT timestamp to seconds"""
    h, m, s = timestamp.replace(',', '.').split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)

def create_subtitle_clips(segments):
    """
    Create simple subtitle clips that display the current spoken text with uniform font size
    """
    font_size = 48  # Increased from 36 to 48
    text_width = 1520
    box_height = 250  # Increased box height to accommodate larger font
    
    subtitle_clips = []
    
    # Create a darker background for better readability
    if segments:
        total_duration = max(end_time for _, end_time, _, _ in segments)
        bg_clip = (ColorClip(size=(text_width, box_height), color=[0, 0, 0])
                  .set_opacity(0.8)
                  .set_position(('center', 'bottom'))
                  .set_duration(total_duration))
        subtitle_clips.append(bg_clip)
    
    # Create a text clip for each segment
    for start_time, end_time, text, _ in segments:
        text_clip = (TextClip(
            text,
            fontsize=font_size,
            font='Arial-Bold',
            color='white',
            align='center',
            method='caption',
            size=(text_width - 120, box_height - 50)  # Slightly adjusted margins for larger text
        )
        .set_position(('center', 'bottom'))
        .margin(bottom=25)  # Increased bottom margin
        .set_start(start_time)
        .set_duration(end_time - start_time))
        
        subtitle_clips.append(text_clip)
    
    return subtitle_clips

def create_video_with_audio(audio_file, background_image, output_file, title="Pride and Prejudice"):
    print(f"\nStarting video creation for {output_file}...")
    
    # Get transcription
    print("1. Transcribing audio...")
    transcript = transcribe_audio(audio_file)
    print("\nTranscript received:")
    print("-" * 50)
    print(transcript)
    print("-" * 50)
    
    segments = parse_srt(transcript)
    print("\nParsed segments:")
    print("-" * 50)
    for i, (start, end, text, _) in enumerate(segments, 1):
        print(f"Segment {i}:")
        print(f"Time: {start:.2f}s -> {end:.2f}s")
        print(f"Text: {text}\n")
    print("-" * 50)
    
    # Resize background image
    print("2. Processing background image...")
    with Image.open(background_image) as img:
        img = img.convert('RGB')
        aspect_ratio = img.height / img.width
        new_height = int(1920 * aspect_ratio)
        resized_img = img.resize((1920, new_height), Image.Resampling.LANCZOS)
        temp_bg = "temp_background.jpg"
        resized_img.save(temp_bg)
    
    # Load audio and background
    print("3. Loading audio and creating background clip...")
    audio = AudioFileClip(audio_file)
    background = (ImageClip(temp_bg)
                 .set_duration(audio.duration))
    
    # Create title and subtitles
    print("4. Creating title and subtitle clips...")
    title_clip = (TextClip(title, 
                          fontsize=70, 
                          color='white',
                          font='Arial-Bold',
                          method='label',
                          bg_color='rgba(0,0,0,0.5)')
                 .set_position(('center', 50))
                 .set_duration(audio.duration))
    print(f"Title clip duration: {title_clip.duration}")
    print(f"Audio duration: {audio.duration}")
    print(f"Segments: {len(segments)}")
    print(f"Segments: {segments}")
    subtitle_clips = create_subtitle_clips(segments)
    
    # Combine all elements
    print("5. Compositing video elements...")
    video = CompositeVideoClip([background, title_clip] + subtitle_clips)
    final_video = video.set_audio(audio)
    
    # Write the video file
    print("6. Writing video file...")
    try:
        final_video.write_videofile(
            output_file,
            fps=24,
            codec='h264_nvenc' if os.system('ffmpeg -hide_banner -encoders | grep -q h264_nvenc') == 0 else 'libx264',
            audio_codec='aac',
            ffmpeg_params=['-preset', 'ultrafast']
        )
        print(f"Successfully created video: {output_file}")
    except Exception as e:
        print(f"Error creating video: {str(e)}")
        raise
    finally:
        # Clean up
        audio.close()
        video.close()
        final_video.close()
        if os.path.exists(temp_bg):
            os.remove(temp_bg)

if __name__ == "__main__":
    audio_file = "pride_and_prejudice_complete.mp3"
    background_image = "background.jpg"
    output_file = "pride_and_prejudice_chapter1.mp4"
    create_video_with_audio(audio_file, background_image, output_file) 