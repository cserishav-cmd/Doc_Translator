"""
Image OCR Processing Module
Handles text extraction from images using Cloud-based APIs (Google Gemini Vision).
No local GPU required - all processing via Internet APIs.
"""

import os
from src.config import llm
from google.api_core.exceptions import ResourceExhausted
from langchain_core.messages import HumanMessage
from PIL import Image
import base64
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def encode_image_to_base64(image_path):
    """
    Convert image file to base64 string for API transmission.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        str: Base64 encoded image string
    """
    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            return base64_image
    except Exception as e:
        print(f"❌ Failed to encode image: {e}")
        raise


def get_image_mime_type(image_path):
    """
    Determine MIME type from image file extension.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        str: MIME type (e.g., 'image/png')
    """
    ext = os.path.splitext(image_path)[1].lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')


def get_languages_for_ocr(target_lang):
    """
    Map target translation language to language names for OCR hint.
    Returns language name for better OCR accuracy.
    """
    lang_map = {
        'hindi': 'Hindi',
        'bengali': 'Bengali',
        'marathi': 'Marathi',
        'tamil': 'Tamil',
        'telugu': 'Telugu',
        'spanish': 'Spanish',
        'french': 'French',
        'german': 'German',
        'japanese': 'Japanese',
        'russian': 'Russian',
        'arabic': 'Arabic',
        'english': 'English'
    }
    
    return lang_map.get(target_lang.lower(), 'English')


def extract_text_from_image(image_path, target_lang='english'):
    """
    Extract text from image using Google Gemini Vision API (cloud-based, no GPU needed).
    
    Args:
        image_path: Path to the image file
        target_lang: Target language for translation (used as OCR hint)
    
    Returns:
        str: Extracted text from the image
    """
    try:
        # Get language hint
        language_hint = get_languages_for_ocr(target_lang)
        print(f"🔍 Performing cloud-based OCR with language hint: {language_hint}")
        
        # Read image file
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        
        # Enhanced OCR prompt for better text extraction
        prompt = f"""You are an expert OCR (Optical Character Recognition) system with exceptional accuracy.

Your task is to extract ALL text from this image with MAXIMUM precision and completeness.

EXTRACTION REQUIREMENTS:
1. Extract text EXACTLY as it appears in the image - character-perfect accuracy
2. Preserve the ORIGINAL LAYOUT including line breaks, spacing, and paragraph structure
3. Do NOT translate, modify, or interpret the text - extract it verbatim
4. The text may be in {language_hint}, English, or multiple languages - handle all correctly
5. Include ALL visible text: headers, titles, body text, captions, labels, and footnotes
6. Maintain proper reading order (top-to-bottom, left-to-right, or appropriate for the language)
7. If no readable text is found, respond with "[NO_TEXT_FOUND]"

OUTPUT FORMAT: Plain text only, preserving the original structure. No commentary, analysis, or additional explanations.

Extract the text now:
"""
        
        # Use Gemini's multimodal capability
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY not found in environment variables")
        
        # Create vision model with explicit API key
        # Using Gemini 2.0 Flash for multimodal (vision) support
        vision_model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",  # ✅ Gemini 2.0 Flash with vision support
            temperature=0.0,  # Deterministic output for OCR
            api_key=api_key  # ✅ Explicitly pass API key to avoid credential errors
        )
        
        # Create message with image
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64.b64encode(image_data).decode()}"
                }
            ]
        )
        
        # Get response
        response = vision_model.invoke([message])
        extracted_text = response.content if hasattr(response, 'content') else str(response)
        
        # Ensure it's a string
        if not isinstance(extracted_text, str):
            extracted_text = str(extracted_text)
        
        # Check if text was found
        if "[NO_TEXT_FOUND]" in extracted_text or not extracted_text.strip():
            raise Exception("No text could be extracted from the image")
        
        print(f"✅ Cloud OCR extracted text successfully")
        print(f"   Length: {len(extracted_text)} characters")
        
        return extracted_text.strip()
    
    except Exception as e:
        print(f"❌ OCR extraction failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def translate_ocr_text(text, target_lang):
    """
    Translate extracted OCR text using LLM.
    
    Args:
        text: Text to translate
        target_lang: Target language for translation
    
    Returns:
        str: Translated text
    """
    try:
        if not text or not text.strip():
            return ""
        
        # Enhanced translation prompt for OCR text
        prompt = f"""You are an expert professional translator specializing in {target_lang}.

Your task is to translate the following OCR-extracted text to {target_lang} with the HIGHEST quality standards.

CONTEXT: This text was extracted from an image using OCR, so focus on producing a clean, fluent translation.

QUALITY REQUIREMENTS:
1. Produce FLUENT, NATURAL-SOUNDING translations that read like they were originally written in {target_lang}
2. Maintain the ORIGINAL MEANING, TONE, and INTENT precisely
3. Use appropriate {target_lang} grammar, vocabulary, idioms, and cultural expressions
4. Preserve ALL formatting including line breaks and paragraph structure
5. Ensure the translation flows naturally and reads smoothly
6. Fix any minor OCR errors while preserving the original meaning
7. Maintain consistency in terminology and style throughout the text

INPUT TEXT:
---
{text}
---

OUTPUT: Provide ONLY the high-quality translated text with no additional commentary, explanations, or metadata.
"""
        
        print(f"🌐 Translating text to {target_lang}...")
        response = llm.invoke(prompt)
        translated_text = response.content if hasattr(response, 'content') else str(response)
        
        if not isinstance(translated_text, str):
            translated_text = str(translated_text)
        
        print(f"✅ Translation completed")
        return translated_text.strip()
    
    except ResourceExhausted:
        raise Exception("Translation failed: You have exceeded your API quota for the day. Please try again later.")
    except Exception as e:
        print(f"❌ Translation failed: {e}")
        raise


def process_image_file(image_path, target_lang, task_id=None, tasks=None):
    """
    Complete pipeline: OCR extraction + Translation for images.
    
    Args:
        image_path: Path to the image file
        target_lang: Target language for translation
        task_id: Optional task ID for progress tracking
        tasks: Optional tasks dictionary for progress updates
    
    Returns:
        dict: Contains original_text, translated_text, and download info
    """
    try:
        # Update progress: Starting OCR
        if task_id and tasks:
            tasks[task_id]["status"] = "processing"
            tasks[task_id]["progress"] = 10
        
        print(f"\n📸 Processing image: {os.path.basename(image_path)}")
        
        # Step 1: Extract text using OCR
        print("Step 1: Extracting text from image...")
        original_text = extract_text_from_image(image_path, target_lang)
        
        if not original_text or not original_text.strip():
            raise Exception("No text could be extracted from the image. The image may be blank or contain no readable text.")
        
        # Update progress: OCR complete
        if task_id and tasks:
            tasks[task_id]["progress"] = 50
        
        # Step 2: Translate the extracted text
        print("Step 2: Translating extracted text...")
        translated_text = translate_ocr_text(original_text, target_lang)
        
        # Update progress: Translation complete
        if task_id and tasks:
            tasks[task_id]["progress"] = 90
        
        # Step 3: Save translated text to file
        output_dir = "storage/translated"
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_filename = f"{base_name}_{target_lang}_translated.txt"
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"=== ORIGINAL TEXT ===\n\n{original_text}\n\n")
            f.write(f"=== TRANSLATED TEXT ({target_lang.upper()}) ===\n\n{translated_text}\n")
        
        print(f"✅ Saved translation to: {output_filename}")
        
        # Update progress: Complete
        if task_id and tasks:
            tasks[task_id]["progress"] = 100
        
        return {
            "original_text": original_text,
            "translated_text": translated_text,
            "translated_text_file": output_filename,
            "download_url": f"/download/{output_filename}"
        }
    
    except Exception as e:
        print(f"❌ Image processing failed: {e}")
        if task_id and tasks:
            tasks[task_id]["status"] = "error"
            tasks[task_id]["error"] = str(e)
        raise
