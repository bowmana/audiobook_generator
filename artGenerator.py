from openai import OpenAI, OpenAIError, RateLimitError, APIConnectionError
import os
from dotenv import load_dotenv
from pathlib import Path
import json
from openaihelpers import retry_on_rate_limit, log_retry_status

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("SECRET_KEY"))

# Add this after the imports
json_schema = {
    "type": "object",
    "properties": {
        "scene_description": {"type": "string"},
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string", "enum": ["main", "supporting"]},
                    "description": {"type": "string"},
                    "first_appearance": {"type": "boolean"},
                    "physical_attributes": {
                        "type": "object",
                        "properties": {
                            "hair_color": {"type": ["string", "null"]},
                            "age": {"type": ["string", "null"]},
                            "race": {"type": ["string", "null"]},
                            "build": {"type": ["string", "null"]}
                        },
                        "required": ["hair_color", "age", "race", "build"]
                    }
                },
                "required": ["name", "role", "description", "first_appearance", "physical_attributes"]
            }
        },
        "time_of_day": {"type": ["string", "null"]},
        "weather": {"type": ["string", "null"]},
        "mood": {"type": ["string", "null"]},
        "key_elements": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["scene_description", "characters", "mood", "key_elements"]
}

def analyze_text_context(title, text_chunk):
    """Analyze the text chunk to understand its context within the book"""
    
    prompt = f"""
    Book Title: {title}
    Text Chunk: {text_chunk}
    
    Analyze this text chunk and provide:
    1. A scene description including setting and time period
    2. Any characters present, including:
       - Their roles (main/supporting)
       - Detailed physical descriptions (hair color, age, race, build)
       - Whether this is their first appearance
       Note: For well-known characters from classic literature, please include their canonical physical descriptions
       even if not mentioned in this specific text chunk. For example:
       - Elizabeth Bennet: Dark hair, 20 years old, English, slender build with fine eyes
       - Mr. Darcy: Dark hair, around 28 years old, English, tall and handsome build
       - Atticus Finch: Gray hair, 40 years old, American, tall and slender build with a strong jawline
       
    3. Time of day and weather conditions
    4. The primary mood or atmosphere
    5. Key visual elements that should be depicted
    
    Provide your analysis in JSON format matching the provided schema. Never leave physical attributes as null for main characters
    from well-documented classic literature - use their canonical descriptions instead.
    """
    
    def _do_analysis():
        return client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", 
                 "content": f"You are a literary analyst and art director. Respond only with valid JSON adhering to this schema: {json.dumps(json_schema)}"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
    
    # Use retry mechanism
    estimated_tokens = len(text_chunk.split()) * 2 + len(json.dumps(json_schema)) // 4
    response = retry_on_rate_limit(_do_analysis, estimated_tokens=estimated_tokens)
    
    if response is None:
        return None
        
    try:
        analysis = json.loads(response.choices[0].message.content)
        return analysis
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {str(e)}")
        return None

def generate_scene_image(analysis, title):
    """Generate an image based on the scene analysis"""
    
    image_prompt = f"""
    Create a detailed artistic scene for the book '{title}':
    {analysis}
    
    Style guidelines:
    - Classical oil painting style with atmospheric, cinematic lighting
    - Only include characters who are actively present in this specific scene analysis
    - Focus on the overall setting and emotional atmosphere described in the specific scene
    - Do not include any text, captions, or labels in the image
    - Create a professional book illustration that captures the period-accurate details
    - Emphasize mood through lighting and color
    - Avoid complex details or busy backgrounds
    - Focus on environmental storytelling and mood
    - If people are present, show them from a distance if possible
    - Emphasize architecture, nature, and lighting
    - Use atmospheric perspective and depth
    - Avoid detailed faces or close-up character portraits
    - Create subtle, suggestive scenes that let viewers imagine details
    """
    
    def _generate_image(prompt):
        return client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
    
    # Use retry mechanism
    estimated_tokens = len(image_prompt.split()) * 2 + 100  # Base DALL-E overhead
    response = retry_on_rate_limit(_generate_image, image_prompt, estimated_tokens=estimated_tokens)
    
    if response is None:
        return None
        
    return response.data[0].url

def save_image(image_url, chunk_number):
    """Save the generated image locally"""
    import requests
    
    # Create images directory if it doesn't exist
    Path("generated_images").mkdir(exist_ok=True)
    
    # Download and save the image
    response = requests.get(image_url)
    image_path = f"generated_images/scene_{chunk_number}.png"
    
    with open(image_path, "wb") as f:
        f.write(response.content)
    
    return image_path

def generate_book_art(title, text_chunk, chunk_number):
    """Main function to generate art for a book chunk"""
    print(f"\nAnalyzing text chunk {chunk_number}...")
    analysis = analyze_text_context(title, text_chunk)
    
    print("\nAI Analysis:")
    print("-" * 50)
    print(analysis)
    print("-" * 50)
    
    print("\nGenerating image based on analysis...")
    image_url = generate_scene_image(analysis, title)
    
    if image_url is None:
        print(f"Failed to generate image for chunk {chunk_number}")
        return None
        
    print("Saving image...")
    image_path = save_image(image_url, chunk_number)
    
    return image_path

if __name__ == "__main__":
    # Example usage
    title = "Pride and Prejudice"
    
    # Reference the text chunks from textToSpeech.py
    with open('pride_and_prejudice.txt', 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    # Using the same chunk size as textToSpeech.py
    chunk_size = 4000
    chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
    
    # Generate art for each chunk
    for i, chunk in enumerate(chunks):
        print(f"\nProcessing chunk {i+1} of {len(chunks)}")
        image_path = generate_book_art(title, chunk, i+1)
        print(f"Generated image saved to: {image_path}") 