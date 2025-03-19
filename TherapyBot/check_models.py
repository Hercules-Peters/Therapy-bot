# test_gemini.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key available: {'Yes' if api_key else 'No'}")

genai.configure(api_key=api_key)

# List available models
try:
    models = genai.list_models()
    print("Available models:")
    for model in models:
        print(f"- {model.name}")
        print(f"  Supported methods: {model.supported_generation_methods}")
except Exception as e:
    print(f"Error listing models: {e}")

# Test a simple generation
try:
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content("Hello, how are you?")
    print("\nTest response:")
    print(response.text)
except Exception as e:
    print(f"Error generating content: {e}")