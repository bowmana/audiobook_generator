import requests
from bs4 import BeautifulSoup
import nltk

# Download required NLTK data
# nltk.download('punkt')
# nltk.download('punkt_tab')

def get_gutenberg_text(url, title):
    response = requests.get(url)
    raw = response.text
    
    # Create a clean filename from the title (remove special chars, lowercase, use underscores)
    filename = f"{title.lower().replace(' ', '_')}.txt"
    
    # Clean the text by removing underscores
    cleaned_text = raw.replace('_', ' ')
    
    # Write the cleaned text to a file
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(cleaned_text)
    
    print(f"Text saved to {filename}")
    return cleaned_text

url = "https://www.gutenberg.org/files/1342/1342-0.txt"
title = "Pride and Prejudice"
book_text = get_gutenberg_text(url, title)

# Test to see if it's working
print(f"Total tokens: {len(book_text)}")
print(f"First 20 tokens: {book_text[:20]}")
print(f"Last 20 tokens: {book_text[-20:]}")
