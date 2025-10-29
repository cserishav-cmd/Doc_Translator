from flask import Flask, render_template, request, redirect, send_from_directory, url_for, jsonify
import os
import threading
import uuid
from src.pipeline import process_file
from src.image_ocr import process_image_file
from src.config import llm
from google.api_core.exceptions import ResourceExhausted
from multiprocessing import Manager  # <-- ADDED: For sharing state between processes

app = Flask(__name__)

UPLOAD_FOLDER = "storage/uploads"
TRANSLATED_FOLDER = "storage/translated"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSLATED_FOLDER, exist_ok=True)

# --- NEW: In-memory task tracker ---
# In a production app, you'd use a database or Redis
# --- MODIFIED: Use a multiprocessing.Manager.dict to share state between Gunicorn workers ---
manager = Manager()
tasks = manager.dict()


def run_translation_task(task_id, file_path, target_lang, output_format=None):
    """
    Enhanced wrapper for document translation with format conversion support.
    """
    global tasks
    try:
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["progress"] = 0
        
        # Pass output_format to process_file
        translated_file_paths_dict = process_file(
            file_path, 
            target_lang, 
            output_format,  # NEW parameter
            task_id, 
            tasks
        )
        
        # Extract the translated file path
        # translated_file_paths_dict structure: {target_lang: filename} e.g., {"hindi": "document_hindi.pdf"}
        translated_file = None
        if translated_file_paths_dict:
            # The dict contains target_lang as key and filename as value
            if target_lang in translated_file_paths_dict:
                translated_file = translated_file_paths_dict[target_lang]
            else:
                # Fallback: get the first available value
                for lang, filename in translated_file_paths_dict.items():
                    if filename:
                        translated_file = filename
                        break
        
        # Check if file was actually created
        if translated_file:
            file_exists = os.path.exists(os.path.join(TRANSLATED_FOLDER, translated_file))
            if not file_exists:
                raise Exception(f"Translated file '{translated_file}' was not found in storage")
        
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 100
        tasks[task_id]["output_files"] = translated_file_paths_dict
        tasks[task_id]["translated_file"] = translated_file
        
        # Add download URL if file exists
        if translated_file:
            tasks[task_id]["download_url"] = f"/download/{translated_file}"
            print(f"✅ Translation completed. Download URL: {tasks[task_id]['download_url']}")
        else:
            raise Exception("No translated file was generated")

    except ResourceExhausted:
        print("❌ ERROR: API quota exceeded.")
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = "Translation failed: You have exceeded your API quota for the day. Please try again later."
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = f"An unexpected error occurred: {str(e)}"


def run_image_ocr_task(task_id, file_path, target_lang):
    """
    Wrapper for image OCR and translation processing.
    """
    global tasks
    try:
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["progress"] = 0
        
        # Process image with OCR
        result = process_image_file(file_path, target_lang, task_id, tasks)
        
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 100
        tasks[task_id]["original_text"] = result["original_text"]
        tasks[task_id]["translated_text"] = result["translated_text"]
        tasks[task_id]["translated_text_file"] = result["translated_text_file"]
        tasks[task_id]["download_url"] = result["download_url"]
        
        print(f"✅ Image OCR and translation completed. Download URL: {result['download_url']}")

    except ResourceExhausted:
        print("❌ ERROR: API quota exceeded.")
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = "Translation failed: You have exceeded your API quota for the day. Please try again later."
    except Exception as e:
        print(f"❌ Image OCR error: {e}")
        import traceback
        traceback.print_exc()
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = f"Image processing failed: {str(e)}"


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
@app.route("/upload_document", methods=["POST"])
def upload_document():
    """
    Upload handler for PDF and DOCX documents.
    """
    global tasks
    
    if "file" not in request.files:
        return jsonify({"error": "No file part in request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    # Type assertion for linter - file.filename is guaranteed to be str here
    filename: str = file.filename if file.filename else "document.pdf"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    print(f"✅ Uploaded document to {file_path}")

    try:
        target_lang = request.form.get("target_lang", "hindi")
        output_format = request.form.get("output_format", None)
        print(f"✅ Target: {target_lang}, Format: {output_format or 'original'}")
        
        # Create task
        task_id = str(uuid.uuid4())
        tasks[task_id] = {"status": "starting", "progress": 0}

        # Start the background thread for document translation
        thread = threading.Thread(
            target=run_translation_task,
            args=(task_id, file_path, target_lang, output_format)
        )
        thread.start()
        
        # Return the task_id to the client
        return jsonify({"task_id": task_id})

    except Exception as e:
        print(f"❌ An unexpected error occurred during document upload: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/upload_image", methods=["POST"])
def upload_image():
    """
    Upload handler for image files (PNG, JPG, JPEG) with OCR processing.
    """
    global tasks
    
    if "file" not in request.files:
        return jsonify({"error": "No file part in request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    # Type assertion for linter
    filename: str = file.filename if file.filename else "image.png"
    
    # Validate image file extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg']:
        return jsonify({"error": "Invalid file type. Please upload PNG, JPG, or JPEG images."}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    print(f"✅ Uploaded image to {file_path}")

    try:
        target_lang = request.form.get("target_lang", "hindi")
        print(f"✅ Target language for OCR: {target_lang}")
        
        # Create task
        task_id = str(uuid.uuid4())
        tasks[task_id] = {"status": "starting", "progress": 0}

        # Start the background thread for image OCR
        thread = threading.Thread(
            target=run_image_ocr_task,
            args=(task_id, file_path, target_lang)
        )
        thread.start()
        
        # Return the task_id to the client
        return jsonify({"task_id": task_id})

    except Exception as e:
        print(f"❌ An unexpected error occurred during image upload: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/status/<task_id>")
@app.route("/task_status/<task_id>")
def status(task_id):
    """
    Route that allows the client to poll for the status of a task.
    Supports both /status/<task_id> and /task_status/<task_id> routes.
    """
    global tasks
    task = tasks.get(task_id)
    if not task:
        return jsonify({"status": "not_found"}), 404
    
    return jsonify(task)


@app.route("/download/<filename>")
def download(filename):
    """
    Download translated file from storage.
    """
    try:
        file_path = os.path.join(TRANSLATED_FOLDER, filename)
        if not os.path.exists(file_path):
            print(f"❌ Download failed: File not found - {file_path}")
            return jsonify({"error": "File not found"}), 404
        
        print(f"✅ Serving download: {filename}")
        return send_from_directory(TRANSLATED_FOLDER, filename, as_attachment=True)
    except Exception as e:
        print(f"❌ Download error: {e}")
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

@app.route("/translate_text", methods=["POST"])
def translate_text_route():
    """
    NEW: Route for text translation without file upload.
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        target_lang = data.get('target_lang', 'hindi')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Use the LLM to translate text directly
        prompt = f"""
        You are a professional translator. Translate the following text to {target_lang}.
        Preserve any formatting, line breaks, and maintain the original tone.
        
        TEXT TO TRANSLATE:
        ---
        {text}
        ---
        
        Provide only the translated text without any additional commentary.
        """
        
        response = llm.invoke(prompt)
        translated_text = response.content if hasattr(response, 'content') else str(response)
        
        # Ensure translated_text is a string
        if not isinstance(translated_text, str):
            translated_text = str(translated_text)
        
        return jsonify({
            "translated_text": translated_text.strip(),
            "original_text": text,
            "target_lang": target_lang
        })
    
    except ResourceExhausted:
        return jsonify({"error": "Translation failed: You have exceeded your API quota for the day. Please try again later."}), 429
    except Exception as e:
        print(f"❌ Text translation error: {e}")
        return jsonify({"error": f"Translation failed: {str(e)}"}), 500

if __name__ == "__main__":
    # Run on 0.0.0.0 to make it accessible on your network
    # Your friends can connect using your computer's IP address and port 5000
    # --- FIX: Changed host to 127.0.0.1 for better tunnel compatibility ---
    
    # --- MODIFIED: Make port/host configurable via environment variables ---
    # Defaults to 0.0.0.0 and port 8080 (or $PORT)
    port = int(os.environ.get('PORT', 8080))
    # --- MODIFIED: Bind to 0.0.0.0 by default for container/deployment compatibility ---
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Note: When running with "python app.py", the manager is not strictly
    # necessary, but it's required for Gunicorn.
    app.run(debug=True, host=host, port=port)

