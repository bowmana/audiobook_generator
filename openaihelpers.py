import time
import math
from datetime import datetime

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
