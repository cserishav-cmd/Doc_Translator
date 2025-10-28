# src/config.py

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# 1. Load environment variables from .env file
load_dotenv()

# 2. Retrieve API Key
api_key = os.getenv("GEMINI_API_KEY")

# 3. Initialize Model, checking for key first
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY environment variable not found. Please ensure your .env file is correctly set up.")
    llm = None
else:
    # ✅ Create the model instance
    llm = ChatGoogleGenerativeAI(
        # ------------------
        # FIX: Using a valid, high-quality model to prevent 404 error
        # ------------------
        model="gemini-2.5-flash-preview-09-2025", 
        temperature=0.1,
        api_key=api_key 
    )

    print("✅ Gemini model loaded successfully.")

