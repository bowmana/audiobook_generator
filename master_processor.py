import os
from pathlib import Path
from bookScrape import get_gutenberg_text
from artGenerator import generate_book_art
from textToSpeech import generate_audio, split_text_into_chunks
from createVideo import create_video_with_audio
from moviepy.editor import concatenate_videoclips, VideoFileClip
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("SECRET_KEY"))

def process_chunk(chunk, chunk_number, total_chunks, title):
    """Process a single chunk completely before moving to the next"""
    print(f"\n{'='*80}")
    print(f"Processing chunk {chunk_number} of {total_chunks}")
    print(f"{'='*80}")
    
    try:
        # Step 1: Generate art
        print(f"\nStep 1: Generating art for chunk {chunk_number}...")
        image_path = generate_book_art(title, chunk, chunk_number)
        if image_path is None:
            print(f"Failed to generate art for chunk {chunk_number}")
            return None
            
        # Step 2: Generate audio
        print(f"\nStep 2: Generating audio for chunk {chunk_number}...")
        audio_path = generate_audio(chunk, chunk_number)
        if audio_path is None:
            print(f"Failed to generate audio for chunk {chunk_number}")
            return None
            
        # Step 3: Create video with subtitles
        print(f"\nStep 3: Creating video for chunk {chunk_number}...")
        video_output = f"chapter_{chunk_number}.mp4"
        print(f"Starting video creation process for {video_output}...")
        print(f"Using audio file: {audio_path}")
        print(f"Using image file: {image_path}")
        
        create_video_with_audio(
            audio_file=str(audio_path),
            background_image=image_path,
            output_file=video_output,
            title=f"{title} - Part {chunk_number}"
        )
        
        if os.path.exists(video_output):
            print(f"Video file successfully created: {video_output}")
            print(f"Video file size: {os.path.getsize(video_output)} bytes")
        else:
            print(f"Warning: Video file {video_output} was not created!")
            
        print(f"\nCompleted processing chunk {chunk_number}")
        print(f"{'='*80}\n")
        
        return video_output
        
    except Exception as e:
        print(f"Error processing chunk {chunk_number}: {str(e)}")
        raise

def process_book(url, title):
    """Main function to process the entire book"""
    print("1. Scraping book text...")
    book_text = get_gutenberg_text(url, title)
    
    print("2. Splitting text into chunks...")
    chunks = split_text_into_chunks(book_text)
    
    all_video_parts = []
    
    # Process each chunk completely before moving to the next
    for i, chunk in enumerate(chunks, 1):
        video_part = process_chunk(chunk, i, len(chunks), title)
        all_video_parts.append(video_part)
    
    # Combine all video parts
    print("\n4. Combining all video parts...")
    final_output = f"{title.lower().replace(' ', '_')}_complete.mp4"
    combine_videos(all_video_parts, final_output)
    
    # Cleanup temporary files
    cleanup_temp_files(all_video_parts)
    
    print(f"\nComplete book processing finished! Final output: {final_output}")

def combine_videos(video_parts, output_file):
    """Combine multiple video parts into one"""
    clips = [VideoFileClip(part) for part in video_parts]
    final_video = concatenate_videoclips(clips)
    final_video.write_videofile(
        output_file,
        fps=24,
        codec='libx264',
        audio_codec='aac'
    )
    
    # Close all clips to free up resources
    for clip in clips:
        clip.close()

def cleanup_temp_files(video_parts):
    """Remove temporary files"""
    # Remove individual video parts
    for video in video_parts:
        if os.path.exists(video):
            os.remove(video)
    
    # Remove temporary audio files
    for file in Path().glob("pride_and_prejudice_part_*.mp3"):
        file.unlink()
    
    # Remove temporary image files
    for file in Path("generated_images").glob("scene_*.png"):
        file.unlink()

if __name__ == "__main__":
    url = "https://www.gutenberg.org/files/1342/1342-0.txt"
    title = "Pride and Prejudice"
    process_book(url, title) 