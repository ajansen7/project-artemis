import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: No API key found. Please set GOOGLE_API_KEY in your .env file.")
    exit(1)

client = genai.Client(api_key=api_key)

print("Available Gemini Models:")
print("-" * 40)

try:
    models = client.models.list()
    for model in models:
        print(f"• {model.name}")
except Exception as e:
    print(f"Error fetching models: {e}")
