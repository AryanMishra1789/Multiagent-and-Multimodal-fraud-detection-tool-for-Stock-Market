
import os
import requests
from dotenv import load_dotenv

# Always load .env from the backend directory
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def gemini_llm(prompt, context=None):
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY,
    }
    parts = [{"text": prompt}]
    if context:
        parts.insert(0, {"text": context})
    data = {"contents": [{"parts": parts}]}
    r = requests.post(endpoint, headers=headers, json=data)
    r.raise_for_status()
    return r.json()['candidates'][0]['content']['parts'][0]['text']
