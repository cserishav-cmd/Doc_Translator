# **Document Translator**

Document Translator is a web-based application built with Python and Flask that allows users to translate entire documents (.pdf, .docx) and images (.png, .jpg) into various languages.

A key feature of this project is its focus on high-fidelity translation, preserving the original document structure and embedding appropriate fonts for complex scripts, such as Devanagari (for Hindi, Marathi) and Bengali.

## **Key Features**

* **Multi-Format Support:** Translate PDF, DOCX, and plain text files.  
* **Image Translation (OCR):** Extracts text from images using Optical Character Recognition (OCR) and translates it.  
* **Font Preservation:** Intelligently embeds fonts (like Noto Sans Devanagari) into translated documents to ensure correct rendering of Indian and other non-Latin languages.  
* **Web-Based Interface:** Simple web UI to upload files and select a target language.  
* **Extensible Pipeline:** The src/ directory contains a modular pipeline for easy maintenance and adding new features.

## **Project Structure**

Doc\_Translator/  
│  
├── app.py                  \# Main Flask application (entry point)  
├── requirements.txt        \# Python dependencies  
├── .gitignore              \# Files to be ignored by Git  
├── README.md               \# You are here\!  
│  
├── src/                    \# Source code for the translation logic  
│   ├── translator.py       \# Core translation functions  
│   ├── image\_ocr.py        \# OCR and image processing  
│   ├── document\_analyzer.py \# Logic for parsing DOCX/PDF  
│   ├── rebuild.py          \# Functions to rebuild the translated file  
│   └── ...                 \# Other helper modules  
│  
├── templates/  
│   └── index.html          \# Frontend HTML  
│  
├── static/  
│   └── css/style.css       \# Frontend CSS  
│  
├── fonts/                  \# Font files (.ttf) used for embedding  
│  
├── storage/                \# (Must be created manually)  
│   ├── uploads/            \# Default location for user uploads  
│   └── translated/         \# Default location for translated files  
│  
└── tests/                  \# Unit and integration tests  
    └── ...

## **Setup and Installation**

Follow these steps to run the project on your local machine.

### **1\. Prerequisites**

* Python 3.8 or newer  
* Git

### **2\. Installation Steps**

1. Clone the repository:  
   (Once you have uploaded it to GitHub, this is the command others will use)  
   git clone \[https://github.com/YOUR\_USERNAME/Doc\_Translator.git\](https://github.com/YOUR\_USERNAME/Doc\_Translator.git)  
   cd Doc\_Translator

2. **Create and activate a virtual environment:**  
   * This isolates the project's dependencies.

*On Windows:*python \-m venv venv  
.\\venv\\Scripts\\activate  
*On macOS/Linux:*python3 \-m venv venv  
source venv/bin/activate

3. **Install dependencies:**  
   pip install \-r requirements.txt

4. **Create required storage folders:**  
   * These folders are ignored by Git (via .gitignore) but are required by the application to store files.

mkdir storage  
mkdir storage\\uploads  
mkdir storage\\translated

5. **Set up Environment Variables:**  
   * This project requires an .env file for configuration (like API keys).  
   * Create a file named .env in the root of the project (Doc\_Translator/.env).  
   * Add your configuration variables to this file (copy them from your original file).  
   * **Example .env content:**  
     \# This is just an example  
     \# Add your actual API keys or settings here  
     TRANSLATION\_API\_KEY="your\_secret\_key\_here"  
     FLASK\_ENV="development"

### **3\. Running the Application**

Once all dependencies are installed and your .env file is ready:

1. **Run the Flask app:**  
   python app.py

2. Open your browser:  
   Navigate to http://127.0.0.1:5000 (or the port specified in your app.py or .env).

## **Running Tests**

To run the project's tests, use pytest:

pytest

## **License**

This project is not currently licensed. You can add an LICENSE file to the repository to specify how others can use your code.