import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from openaihelpers import estimate_tokens, retry_on_rate_limit

load_dotenv() 
SECRET_KEY = os.getenv("SECRET_KEY")

def read_full_text(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()

def split_text_into_chunks(text, chunk_size=4000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def generate_audio(chunk, chunk_number):
    client = OpenAI(api_key=SECRET_KEY)
    speech_file_path = Path(f"pride_and_prejudice_part_{chunk_number}.mp3")
    
    def _do_tts(text):
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        response.stream_to_file(speech_file_path)
        return speech_file_path
    
    estimated_tokens = estimate_tokens(chunk)
    print(f"Generating audio for chunk {chunk_number}...")
    return retry_on_rate_limit(_do_tts, chunk, estimated_tokens=estimated_tokens)

if __name__ == "__main__":
    # This code only runs if the file is executed directly
    full_text = read_full_text('pride_and_prejudice.txt')
    chunks = split_text_into_chunks(full_text)
    
    for i, chunk in enumerate(chunks, 1):
        generate_audio(chunk, i)