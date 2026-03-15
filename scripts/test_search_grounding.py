import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

async def test_search():
    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        response = await client.aio.models.generate_content(
            model=model_name,
            contents="Find recent AI Product Manager job openings at Braintrust or Confident AI.",
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}]
            )
        )
        print("Response Text:", response.text)
        print("Candidates 0 groundings:", list(response.candidates[0].grounding_metadata.grounding_chunks))
    except Exception as e:
        print("Error with tools=[{'google_search': {}}] :", e)

if __name__ == "__main__":
    asyncio.run(test_search())
