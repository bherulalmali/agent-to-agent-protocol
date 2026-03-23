import os
import logging
from dotenv import load_dotenv
from google.genai import Client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_POC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(_POC_ROOT, ".env"))

def check_models():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in .env")
        return

    print(f"🔍 Testing API Key: {api_key[:4]}...{api_key[-4:]}")
    client = Client(api_key=api_key)

    try:
        print("Listing available models:")
        for model in client.models.list():
            # The model name usually comes prefixed with 'models/' from this SDK
            print(f" - {model.name}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == "__main__":
    check_models()
