import os
from pathlib import Path
from pydub import AudioSegment

def get_mp3_files(prefix):
    # Get all MP3 files in the current directory that match our prefix
    files = [f for f in os.listdir() if f.endswith('.mp3') and f.startswith(prefix)]
    
    # Sort files based on the part number
    files.sort(key=lambda x: int(x.split('part_')[1].split('.')[0]))
    return files

def combine_audio_files(prefix="pride_and_prejudice"):
    files = get_mp3_files(prefix)
    
    if not files:
        print(f"No MP3 files found with prefix: {prefix}")
        return
    
    print(f"Found {len(files)} files to combine")
    
    # Load the first audio file
    combined = AudioSegment.from_mp3(files[0])
    print(f"Starting with: {files[0]}")
    
    # Append each subsequent file
    for file in files[1:]:
        print(f"Appending: {file}")
        audio = AudioSegment.from_mp3(file)
        combined += audio
    
    # Export the combined file
    output_filename = f"{prefix}_complete.mp3"
    combined.export(output_filename, format="mp3")
    print(f"Created combined file: {output_filename}")

if __name__ == "__main__":
    combine_audio_files() 