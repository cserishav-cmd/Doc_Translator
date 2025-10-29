from flask import Flask, render_template, request, redirect, send_from_directory, url_for, jsonify
import os
import threading
import uuid
from src.pipeline import process_file
from src.image_ocr import process_image_file
from src.config import llm
from google.api_core.exceptions import ResourceExhausted

app = Flask(__name__)

UPLOAD_FOLDER = "storage/uploads"
TRANSLATED_FOLDER = "storage/translated"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSLATED_FOLDER, exist_ok=True)

# In-memory task tracker
tasks = {}

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
            output_format,
            task_id, 
            tasks
        )
        
        # Extract the translated file path
        if not translated_file_paths_dict or target_lang not in translated_file_paths_dict:
            raise Exception(f"Translation output file not found for lang: {target_lang}")

        translated_file_path = translated_file_paths_dict[target_lang]
        
        tasks[task_id]["status"] = "complete"
        tasks[task_id]["progress"] = 100
        tasks[task_id]["download_url"] = f"/download/{os.path.basename(translated_file_path)}"
        tasks[task_id]["result_file"] = os.path.basename(translated_file_path)

    except ResourceExhausted:
        print(f"⛔ Quota Exceeded for task {task_id}")
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error_message"] = "API Quota Exceeded. Please try again later."
    except Exception as e:
        print(f"❌ Error in task {task_id}: {e}")
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error_message"] = str(e)

def run_image_translation_task(task_id, file_path, target_lang):
    """
    Wrapper for image translation task.
    """
    global tasks
    try:
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["progress"] = 10
        
        result = process_image_file(file_path, target_lang, task_id, tasks)
        
        tasks[task_id]["status"] = "complete"
        tasks[task_id]["progress"] = 100
        tasks[task_id]["download_url"] = result["download_url"]
        tasks[task_id]["result_file"] = result["translated_text_file"]
        tasks[task_id]["original_text"] = result["original_text"]
        tasks[task_id]["translated_text"] = result["translated_text"]

    except ResourceExhausted:
        print(f"⛔ Quota Exceeded for task {task_id}")
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error_message"] = "API Quota Exceeded. Please try again later."
    except Exception as e:
        print(f"❌ Error in task {task_id}: {e}")
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error_message"] = str(e)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload_document", methods=["POST"])
def upload_document():
    if "document" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["document"]
    target_lang = request.form.get("target_lang", "Hindi")
    output_format = request.form.get("output_format", "original") # Get format

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file:
        original_filename = file.filename
        file_ext = os.path.splitext(original_filename)[1]
        
        # Save the uploaded file
        upload_path = os.path.join(UPLOAD_FOLDER, original_filename)
        file.save(upload_path)
        
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "status": "pending", 
            "original_file": original_filename
        }
        
        # Check if image file
        image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
        if file_ext.lower() in image_extensions:
            # Start image translation thread
            thread = threading.Thread(
                target=run_image_translation_task, 
                args=(task_id, upload_path, target_lang)
            )
        else:
            # Start document translation thread
            thread = threading.Thread(
                target=run_translation_task, 
                args=(task_id, upload_path, target_lang, output_format)
            )
            
        thread.start()
        
        return jsonify({"task_id": task_id})

@app.route("/task_status/<task_id>")
def task_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(TRANSLATED_FOLDER, filename, as_attachment=True)

@app.route("/translate_text", methods=["POST"])
def translate_text():
    try:
        data = request.json
        text = data.get("text")
        target_lang = data.get("target_lang", "Hindi")
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        if not llm:
             return jsonify({"error": "LLM not initialized. Check API key."}), 500

        # Simple prompt to translate text directly
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
    # --- FIX FOR RENDER ---
    # 1. Bind to '0.0.0.0' to be accessible externally.
    # 2. Use the 'PORT' environment variable provided by Render,
    #    defaulting to 10000 (which you saw in logs) if not set.
    # ----------------------
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
