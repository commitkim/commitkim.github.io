from dotenv import load_dotenv
load_dotenv()
import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

models_to_test = ["gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.0-flash-lite"]
print("\nTesting Generation:")
for model_name in models_to_test:
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Say hi"
        )
        print(f"[{model_name}] Success: {response.text.strip()}")
    except Exception as e:
        print(f"[{model_name}] Error: {e}")
