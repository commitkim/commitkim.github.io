import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# noqa: E402
from google import genai
from core.config import Config


def list_models():
    try:
        cfg = Config.instance()
        api_key = cfg.get_secret("GEMINI_API_KEY")
        if not api_key:
            print("No API Key found in .env via Config.")
            # Fallback to direct check if config fails (shouldn't happen)
            return

        print(f"Using API Key: {api_key[:5]}...")
        client = genai.Client(api_key=api_key)

        print("Listing models via client.models.list()...")
        # Pager object
        pager = client.models.list()

        count = 0
        for m in pager:
            print(f"- {m.name}")
            count += 1
            if count > 50:
                break

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    list_models()
