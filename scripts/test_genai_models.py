from google import genai
from agents.config import settings
client = genai.Client(api_key=settings.google_api_key)

print("Available models:")
for model in client.models.list():
    if "embed" in model.name:
        print(model.name)
