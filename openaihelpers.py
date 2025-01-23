import time
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Union

# Roughly estimate tokens based on text length.
# This is NOT an official formula. Adjust as your usage requires.
def estimate_tokens(text: str, tokens_per_char=0.5) -> int:
    """
    Estimate tokens based on a simple ratio:
    tokens ≈ tokens_per_char * number_of_characters
    """
    return int(tokens_per_char * len(text))

def calculate_wait_time(estimated_tokens: int, tokens_per_minute: int = 30000) -> float:
    """
    Given an approximate token usage and a tokens-per-minute threshold,
    estimate how many minutes to wait before enough tokens are "available."
    """
    minutes_needed = estimated_tokens / tokens_per_minute
    return minutes_needed * 60

def log_retry_status(message: str):
    """Helper function to log retry status with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def retry_on_rate_limit(func, *args, estimated_tokens=None, **kwargs):
    """
    Attempt to call 'func' and implement smart retry logic based on rate limits.
    Will retry up to 10 times with 1 hour waits for both quota and rate limit errors.
    """
    from openai import RateLimitError, OpenAIError
    max_retries = 10
    hourly_wait_time = 3600  # 1 hour in seconds
    
    # Log the function and its parameters
    func_name = func.__name__ if hasattr(func, '__name__') else str(func)
    log_retry_status(f"API Request Details:")
    log_retry_status(f"- Function: {func_name}")
    log_retry_status(f"- Arguments: {args}")
    log_retry_status(f"- Keyword Arguments: {kwargs}")
    
    attempt = 0
    while attempt < max_retries:  # Changed to use max_retries as the limit
        try:
            log_retry_status(f"Attempt {attempt + 1} of {max_retries}: Executing API call...")
            result = func(*args, **kwargs)
            log_retry_status("API call successful!")
            return result
            
        except OpenAIError as e:
            error_message = str(e).lower()
            
            # Handle both quota and rate limit errors the same way
            if ('insufficient_quota' in error_message or 
                'exceeded your current quota' in error_message or 
                isinstance(e, RateLimitError)):
                
                attempt += 1
                if attempt >= max_retries:
                    log_retry_status(f"Maximum retries ({max_retries}) reached")
                    return None
                
                log_retry_status("\nAPI limit exceeded for request:")
                log_retry_status(f"- Function: {func_name}")
                log_retry_status(f"- Arguments: {args}")
                log_retry_status(f"- Keyword Arguments: {kwargs}")
                log_retry_status(f"- Error: {str(e)}")
                log_retry_status(f"- Attempt: {attempt} of {max_retries}")
                log_retry_status(f"\nWaiting 1 hour before retry...")
                
                # Countdown for hourly wait
                start_time = time.time()
                while time.time() - start_time < hourly_wait_time:
                    time_left = hourly_wait_time - (time.time() - start_time)
                    if time_left > 0:
                        log_retry_status(f"Time until next attempt: {time_left/60:.1f} minutes")
                        time.sleep(min(300, time_left))  # Update every 5 minutes
                continue
                
            else:
                log_retry_status(f"Unexpected OpenAI error: {str(e)}")
                raise e  # Only raise for unexpected errors

# Add these constants for price calculations
PRICING = {
    'gpt4': {
        'input': 0.01,  # per 1k tokens
        'output': 0.03  # per 1k tokens
    },
    'dalle3': 0.04,    # per image
    'whisper': 0.006,  # per minute
    'tts': 0.015      # per 1k characters
}

def estimate_tts_cost(text: str) -> Dict[str, Union[int, float]]:
    """
    Estimate cost for text-to-speech conversion
    Returns dict with character count and cost
    """
    char_count = len(text)
    # Convert to thousands and multiply by rate
    cost = (char_count / 1000) * PRICING['tts']
    
    return {
        'characters': char_count,
        'cost': round(cost, 4)
    }

def estimate_transcription_cost(audio_duration_seconds: float) -> Dict[str, Union[float, float]]:
    """
    Estimate cost for audio transcription using Whisper
    Returns dict with duration and cost
    """
    minutes = audio_duration_seconds / 60
    cost = minutes * PRICING['whisper']
    
    return {
        'duration_minutes': round(minutes, 2),
        'cost': round(cost, 4)
    }

def estimate_image_generation_cost(num_images: int = 1) -> Dict[str, Union[int, float]]:
    """
    Estimate cost for DALL-E 3 image generation
    Returns dict with image count and cost
    """
    cost = num_images * PRICING['dalle3']
    
    return {
        'images': num_images,
        'cost': round(cost, 4)
    }

def estimate_text_analysis_cost(text: str) -> Dict[str, Union[int, float]]:
    """
    Estimate cost for GPT-4 text analysis
    Returns dict with token counts and cost
    """
    # Estimate tokens (rough approximation)
    input_tokens = estimate_tokens(text)
    # Assume output is roughly 1/3 of input for scene analysis
    output_tokens = input_tokens // 3
    
    input_cost = (input_tokens / 1000) * PRICING['gpt4']['input']
    output_cost = (output_tokens / 1000) * PRICING['gpt4']['output']
    total_cost = input_cost + output_cost
    
    return {
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'cost': round(total_cost, 4)
    }

def estimate_chunk_processing_cost(chunk: str, audio_duration: float = None) -> Dict[str, Union[dict, float]]:
    """
    Estimate total cost for processing one chunk of text into a video segment
    
    Parameters:
    - chunk: The text chunk to be processed
    - audio_duration: Optional pre-calculated audio duration in seconds
    
    Returns dict with breakdown of costs and total
    """
    # If audio duration not provided, estimate it
    if audio_duration is None:
        # Rough estimate: 3 characters per second
        audio_duration = len(chunk) / 3
    
    # Get individual cost estimates
    tts_estimate = estimate_tts_cost(chunk)
    transcription_estimate = estimate_transcription_cost(audio_duration)
    image_estimate = estimate_image_generation_cost(1)  # One image per chunk
    analysis_estimate = estimate_text_analysis_cost(chunk)
    
    total_cost = (
        tts_estimate['cost'] +
        transcription_estimate['cost'] +
        image_estimate['cost'] +
        analysis_estimate['cost']
    )
    
    return {
        'text_to_speech': tts_estimate,
        'transcription': transcription_estimate,
        'image_generation': image_estimate,
        'text_analysis': analysis_estimate,
        'total_cost': round(total_cost, 4)
    }

def estimate_full_book_cost(text: str, chunk_size: int = 4000) -> Dict[str, Union[dict, float]]:
    """
    Estimate total cost for processing an entire book
    
    Parameters:
    - text: The full book text
    - chunk_size: Size of each chunk to process (default 4000 chars)
    
    Returns dict with breakdown of costs per chunk and total
    """
    # Split text into chunks
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    # Calculate costs for each chunk
    chunk_costs = []
    total_cost = 0
    
    for i, chunk in enumerate(chunks, 1):
        chunk_estimate = estimate_chunk_processing_cost(chunk)
        chunk_costs.append({
            'chunk_number': i,
            'costs': chunk_estimate
        })
        total_cost += chunk_estimate['total_cost']
    
    return {
        'number_of_chunks': len(chunks),
        'chunk_estimates': chunk_costs,
        'total_estimated_cost': round(total_cost, 4)
    }

def print_cost_estimate(estimate: Dict) -> None:
    """
    Pretty print a cost estimate with service totals
    """
    print("\nCost Estimate Breakdown:")
    print("=" * 50)
    
    if 'number_of_chunks' in estimate:
        print(f"\nTotal Chunks: {estimate['number_of_chunks']}")
        
        # Initialize service totals
        totals = {
            'tts': 0.0,
            'transcription': 0.0,
            'image': 0.0,
            'analysis': 0.0
        }
        
        # Print chunk details
        print("\nBreakdown by chunk:")
        for chunk in estimate['chunk_estimates']:
            print(f"\nChunk {chunk['chunk_number']}:")
            costs = chunk['costs']
            print(f"  TTS: ${costs['text_to_speech']['cost']:.3f}")
            print(f"  Transcription: ${costs['transcription']['cost']:.3f}")
            print(f"  Image: ${costs['image_generation']['cost']:.3f}")
            print(f"  Analysis: ${costs['text_analysis']['cost']:.3f}")
            print(f"  Chunk Total: ${costs['total_cost']:.3f}")
            
            # Add to service totals
            totals['tts'] += costs['text_to_speech']['cost']
            totals['transcription'] += costs['transcription']['cost']
            totals['image'] += costs['image_generation']['cost']
            totals['analysis'] += costs['text_analysis']['cost']
        
        # Print service totals
        print("\nTotals by Service:")
        print("=" * 50)
        print(f"Total TTS Cost: ${totals['tts']:.2f}")
        print(f"Total Transcription Cost: ${totals['transcription']:.2f}")
        print(f"Total Image Generation Cost: ${totals['image']:.2f}")
        print(f"Total Text Analysis Cost: ${totals['analysis']:.2f}")
        print("-" * 50)
        print(f"Grand Total: ${estimate['total_estimated_cost']:.2f}")
        
    else:
        print(f"Text-to-Speech: ${estimate['text_to_speech']['cost']:.3f}")
        print(f"Transcription: ${estimate['transcription']['cost']:.3f}")
        print(f"Image Generation: ${estimate['image_generation']['cost']:.3f}")
        print(f"Text Analysis: ${estimate['text_analysis']['cost']:.3f}")
        print("-" * 50)
        print(f"Total Cost: ${estimate['total_cost']:.3f}")
