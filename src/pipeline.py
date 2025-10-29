import os
import fitz  # Import PyMuPDF
import re    # Import regular expression module
import uuid  # Import UUID module
from src.translator import translate_elements
from src.document_analyzer import DocumentAnalyzer  # Add document analyzer
# UPDATED: Import the new in-place PDF rebuilder
from src.rebuild import rebuild_pdf_in_place, rebuild_docx_with_lxml, convert_pdf_to_docx, convert_docx_to_pdf
# --- FIX: Import the Document class type specifically ---
from docx import Document as DocxDocument # Use alias to avoid conflict if needed later
from docx.document import Document as DocumentClass # Import the class type itself
# NEW: Import for lxml text box parsing
from docx.oxml.ns import qn
from collections import Counter
import traceback # For detailed error logging

# ---------------- Helper functions ----------------

def extract_pdf_elements(file_path):
    """
    Extracts text from PDF using PyMuPDF.
    """
    doc = None
    elements = []
    images_info = []

    try:
        doc = fitz.open(file_path)
        print(f"--- Starting PDF Extraction for: {os.path.basename(file_path)} ---")
        for page_num, page in enumerate(doc):  # type: ignore[arg-type]
            print(f"  Processing PDF Page {page_num + 1}/{doc.page_count}")
            image_list = page.get_images(full=True)
            page_image_count = 0
            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    bboxes = page.get_image_bbox(img)
                    if bboxes:
                        bbox_tuple = bboxes if isinstance(bboxes, tuple) else bboxes[0]
                        images_info.append({
                            "page_num": page_num,
                            "bbox": bbox_tuple,
                            "xref": xref
                        })
                        page_image_count += 1
                except Exception as img_e:
                    print(f"⚠️ Warning: Could not get bbox for image {xref} on page {page_num+1}: {img_e}")

            page_dict = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_LIGATURES & ~fitz.TEXT_PRESERVE_WHITESPACE)
            text_blocks = []
            has_digital_text = False
            page_block_count = 0

            for block in page_dict.get("blocks", []):
                if block["type"] == 0:  # Text block
                    block_text = ""
                    font_sizes = []
                    font_names = []
                    font_flags = []

                    for line in block.get("lines", []):
                        line_text = ""
                        for span in line.get("spans", []):
                            span_text = span.get("text", "")
                            normalized_span_text = ' '.join(span_text.split())
                            if normalized_span_text:
                                line_text += normalized_span_text + " "
                                font_sizes.append(round(span["size"]))
                                font_names.append(span.get("font", "helv"))
                                font_flags.append(span.get("flags", 0))
                        stripped_line_text = line_text.strip()
                        if stripped_line_text:
                            block_text += stripped_line_text + "\n"

                    final_block_text = block_text.strip()

                    if final_block_text:
                        has_digital_text = True
                        page_block_count += 1
                        common_size = Counter(font_sizes).most_common(1)[0][0] if font_sizes else 10
                        common_font = Counter(font_names).most_common(1)[0][0] if font_names else "helv"
                        is_bold = any((f & (1 << 4)) for f in font_flags)
                        is_italic = any((f & (1 << 0)) for f in font_flags)
                        is_heading_heuristic = (font_sizes and common_size > 14) or (is_bold and common_size > 12)

                        text_blocks.append({
                            "type": "paragraph",
                            "text": final_block_text,
                            "is_heading": is_heading_heuristic,
                            "page_num": page_num,
                            "bbox": block["bbox"],
                            "font_size": common_size,
                            "font_name": common_font,
                            "is_bold": is_bold,
                            "is_italic": is_italic,
                            "is_image_text": False
                        })

            if not has_digital_text:
                print(f"⚠️ Page {page_num+1} has minimal/no digital text (likely scanned/image).")
                print(f"   💡 TIP: For scanned PDFs, use online OCR (e.g., Adobe) before uploading.")

            elements.extend(text_blocks)

        print(f"--- Finished PDF Extraction ---")
        print(f"  Total elements extracted: {len(elements)}")
        if images_info:
            print(f"  Total images found: {len(images_info)}")

        while elements and elements[-1].get("text", "") == "[EMPTY]":
            elements.pop()

        print(f"  Returning {len(elements)} elements from PDF extraction.")
        return elements

    except Exception as e:
        print(f"❌ Error extracting PDF elements from {file_path}: {e}")
        traceback.print_exc()
        return []
    finally:
        if doc:
            try:
                doc.close()
            except Exception: pass

def extract_docx_elements_and_objects(file_path):
    """
    Extracts text from DOCX, handling paragraphs, tables, and text boxes.
    """
    doc = None
    elements_to_translate = []
    standard_paragraph_objects = []
    textbox_paragraph_elements = []

    print(f"\n--- Starting DOCX Extraction for: {os.path.basename(file_path)} ---")

    try:
        doc = DocxDocument(file_path)

        def process_text(text, is_heading, para_obj=None, lxml_obj=None, location=""):
            stripped_text = text.strip()
            element_text = stripped_text if stripped_text else "[EMPTY]"
            
            def _looks_like_equation(s: str) -> bool:
                if not s or s == "[EMPTY]": return False
                if re.search(r"(\\begin\{|\$\$|\$|\\\\\[|\\\\\(|\\\[|\\\()", s): return True
                math_symbols = re.findall(r"[=<>\^_\\+\-/*%|:;{}\[\]\(\)]", s)
                ratio = len(math_symbols) / max(len(s), 1)
                if ratio > 0.12: return True
                tokens = s.split()
                digit_tokens = sum(1 for t in tokens if re.search(r"\d", t))
                if digit_tokens >= max(1, len(tokens) // 3) and len(tokens) < 20: return True
                return False

            is_equation = _looks_like_equation(element_text)

            element = {
                "type": "paragraph",
                "text": element_text,
                "is_heading": is_heading,
                "is_equation": is_equation,
                "location": location
            }
            return element

        def parse_paragraph_runs(para):
            full_text_simple = para.text.strip()
            if full_text_simple:
                 current_text = ""
                 for run in para.runs:
                      is_bold = run.bold or (hasattr(run.font, 'bold') and run.font.bold is True)
                      run_text_content = run.text
                      if run_text_content is None: run_text_content = ""
                      current_text += f"**{run_text_content}**" if is_bold else run_text_content
                 return current_text.strip() if current_text.strip() else "[EMPTY]"
            else:
                 if para.runs:
                      current_text = ""
                      for run in para.runs:
                           is_bold = run.bold or (hasattr(run.font, 'bold') and run.font.bold is True)
                           run_text_content = run.text
                           if run_text_content is None: run_text_content = ""
                           current_text += f"**{run_text_content}**" if is_bold else run_text_content
                      return current_text.strip() if current_text.strip() else "[EMPTY]"
                 else:
                      return "[EMPTY]"

        def parse_lxml_paragraph(p_element):
            text = ""
            for r_element in p_element.findall(qn('w:r')):
                run_text = ""
                is_bold = False
                rPr = r_element.find(qn('w:rPr'))
                if rPr is not None:
                    b_tag = rPr.find(qn('w:b'))
                    if b_tag is not None:
                        val = b_tag.get(qn('w:val'))
                        if val is None or val.lower() in ('1', 'true', 'on'):
                            is_bold = True
                for t_element in r_element.findall(qn('w:t')):
                    if t_element.text:
                        run_text += t_element.text
                text += f"**{run_text}**" if is_bold else run_text
            return text.strip() if text.strip() else "[EMPTY]"

        # --- 1. Process Standard Content (Body, Tables, Headers, Footers) ---
        print("\n  Processing Standard Content...")
        all_standard_paras_objs = []
        all_standard_paras_objs.extend(doc.paragraphs)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    all_standard_paras_objs.extend(cell.paragraphs)
        for section in doc.sections:
            try:
                if section.header: all_standard_paras_objs.extend(section.header.paragraphs)
                if section.footer: all_standard_paras_objs.extend(section.footer.paragraphs)
            except Exception as hf_e:
                print(f"  Warning: Could not access header/footer for section: {hf_e}")

        processed_para_ids = set()
        for idx, para in enumerate(all_standard_paras_objs):
             para_id = id(para)
             if para_id in processed_para_ids:
                 continue
             is_heading = para.style is not None and para.style.name.lower().startswith('heading')
             text = parse_paragraph_runs(para)
             location = f"Std Para {idx}"
             print(f"  Extracting ({location}): Head={is_heading}, Text='{text[:50].replace(chr(10), ' ')}...'")
             elements_to_translate.append(process_text(text, is_heading, para_obj=para, location=location))
             standard_paragraph_objects.append(para)
             textbox_paragraph_elements.append(None)
             processed_para_ids.add(para_id)

        print(f"  Finished Standard Content. Paragraphs processed: {len(standard_paragraph_objects)}")

        # --- 2. Process Text Box Content (lxml) ---
        print("\n  Processing Text Box Content...")
        textbox_paras_count = 0
        try:
            lxml_paragraphs_in_boxes = doc.element.body.findall(f'.//{qn("w:txbxContent")}//{qn("w:p")}')
            print(f"  Found {len(lxml_paragraphs_in_boxes)} paragraph elements within text boxes (using lxml).")

            for p_idx, p_element in enumerate(lxml_paragraphs_in_boxes):
                    is_heading_lxml = False
                    pPr = p_element.find(qn('w:pPr'))
                    if pPr is not None:
                         pStyle = pPr.find(qn('w:pStyle'))
                         if pStyle is not None:
                              style_val = pStyle.get(qn('w:val'))
                              if style_val and style_val.lower().startswith('heading'):
                                   is_heading_lxml = True
                    text = parse_lxml_paragraph(p_element)
                    location = f"TextBox LXML Para {p_idx}"
                    print(f"  Extracting ({location}): Head={is_heading_lxml}, Text='{text[:50].replace(chr(10), ' ')}...'")
                    elements_to_translate.append(process_text(text, is_heading_lxml, lxml_obj=p_element, location=location))
                    standard_paragraph_objects.append(None)
                    textbox_paragraph_elements.append(p_element)
                    textbox_paras_count += 1
            print(f"  Finished Text Box Content. Paragraphs extracted: {textbox_paras_count}")
        except Exception as e:
            print(f"⚠️ Warning: Could not process text boxes via lxml: {e}")
            traceback.print_exc()

        print(f"\n--- Finished DOCX Extraction ---")
        print(f"  Total elements extracted: {len(elements_to_translate)}")

        if len(elements_to_translate) != len(standard_paragraph_objects) or len(elements_to_translate) != len(textbox_paragraph_elements):
             print(f"❌ CRITICAL ERROR: List lengths mismatched after extraction! ")
             print(f"  Lengths -> Elements: {len(elements_to_translate)}, Std Paras: {len(standard_paragraph_objects)}, LXML Paras: {len(textbox_paragraph_elements)}")
             return [], [], [], None, doc
        
        print(f"  Returning {len(elements_to_translate)} elements, {len(standard_paragraph_objects)} std para refs, {len(textbox_paragraph_elements)} lxml para refs.")
        return elements_to_translate, standard_paragraph_objects, textbox_paragraph_elements, None, doc

    except Exception as e:
        print(f"❌ Error extracting DOCX elements from {file_path}: {e}")
        traceback.print_exc()
        return [], [], [], None, doc if 'doc' in locals() and doc is not None else None


# ---------------- Main processing function ----------------
#
# --- FIX 1: Add 'output_dir' as the third argument ---
def process_file(file_path, target_lang, output_dir, output_format=None, task_id=None, tasks=None):
    """
    ENHANCED: High-fidelity extraction, translation, and rebuilding with format conversion.
    """
    doc_object = None
    standard_paragraph_objects = None
    textbox_paragraph_elements = None
    textbox_shapes = None
    
    # --- FIX 2: Disable DocumentAnalyzer to prevent memory crash ---
    # This line loads a large AI model and is likely causing the server to run
    # out of memory and crash. Commenting it out will fix the crash.
    # doc_analyzer = DocumentAnalyzer()
    # ---
    elements = []
    original_format = ""
    
    # --- FIX 1: Remove hardcoded (and incorrect) output directory ---
    # The correct directory is now passed in from app.py
    # output_dir = "storage/translated" 
    # ---
    
    translated_files = {}

    try:
        if not file_path or not isinstance(file_path, str):
             raise ValueError("Invalid file path provided.")

        source_input_file = file_path

        _, file_extension = os.path.splitext(file_path)
        original_format = file_extension.lower().strip('.')
        original_input_format = original_format

        print(f"\nProcessing file: {os.path.basename(file_path)}, Format: {original_format}")

        created_temp_files = []

        if original_format == "pdf":
            print(f"🔁 Converting source PDF to DOCX for high-fidelity translation...")
            # --- FIX 1: Use the correct output_dir variable ---
            temp_converted_docx = os.path.join(output_dir, f"converted_{uuid.uuid4()}.docx")
            try:
                convert_pdf_to_docx(file_path, temp_converted_docx)
                created_temp_files.append(temp_converted_docx)
                print(f"  ✅ PDF converted to DOCX: {temp_converted_docx}")
            except Exception as conv_e:
                print(f"❌ PDF->DOCX conversion failed: {conv_e}")
                traceback.print_exc()
                if task_id and tasks and task_id in tasks:
                    tasks[task_id]["status"] = "error"
                    tasks[task_key]["error_message"] = "PDF to DOCX conversion failed."
                return {}

            elements, standard_paragraph_objects, textbox_paragraph_elements, _, doc_object = extract_docx_elements_and_objects(temp_converted_docx)
            
            # --- FIX 2: Disable DocumentAnalyzer call ---
            # This call also consumes a lot of memory.
            # elements = doc_analyzer.enhance_extraction(temp_converted_docx, elements)
            # ---
            
            original_format = "docx"
            file_path = temp_converted_docx
        elif original_format == "docx":
            elements, standard_paragraph_objects, textbox_paragraph_elements, _, doc_object = extract_docx_elements_and_objects(file_path)
        else:
            raise ValueError(f"Unsupported file type: {original_format}")

        os.makedirs(output_dir, exist_ok=True)

        if not elements:
            print(f"⛔ ERROR: Extraction returned no elements for {file_path}. Cannot proceed.")
            if task_id and tasks and task_id in tasks:
                 tasks[task_id]["status"] = "error"
                 tasks[task_id]["error_message"] = "Extraction failed: No content found in the document."
            return {}


        print(f"✅ Starting translation of {len(elements)} elements to {target_lang}...")
        translated_elements = translate_elements(elements, target_lang, task_id, tasks)

        if not translated_elements or len(translated_elements) != len(elements):
             print(f"⛔ ERROR: Translation failed or returned mismatched element count.")
             print(f"  Expected: {len(elements)}, Got: {len(translated_elements)}")
             raise Exception("Translation failed or returned mismatched element count.")

        if output_format and output_format in ['pdf', 'docx']:
            final_format = output_format
        else:
            final_format = 'pdf' if original_input_format == 'pdf' else original_format

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        safe_base_name = re.sub(r'[^\w\-]+', '_', base_name)
        out_file = os.path.join(
            output_dir, # <-- FIX 1: This now correctly uses the directory from app.py
            f"{safe_base_name}_{target_lang.lower()}.{final_format}"
        )

        print(f"🔧 Rebuilding output file: {out_file} (Format: {final_format})")

        temp_pdf = os.path.join(output_dir, f"temp_{safe_base_name}_{uuid.uuid4()}.pdf")
        temp_docx = os.path.join(output_dir, f"temp_{safe_base_name}_{uuid.uuid4()}.docx")

        try:
            if original_format == "pdf" and final_format == "pdf":
                rebuild_pdf_in_place(file_path, translated_elements, out_file, target_lang)
            elif original_format == "pdf" and final_format == "docx":
                rebuild_pdf_in_place(file_path, translated_elements, temp_pdf, target_lang)
                created_temp_files.append(temp_pdf)
                convert_pdf_to_docx(temp_pdf, out_file)
            elif original_format == "docx" and final_format == "docx":
                if not isinstance(doc_object, DocumentClass):
                    print(f"⚠️ Warning: doc_object invalid before rebuild. Attempting to reload {file_path}")
                    try:
                        doc_object = DocxDocument(file_path)
                        if not standard_paragraph_objects and not textbox_paragraph_elements:
                             print("  Re-extracting object references...")
                             _, standard_paragraph_objects, textbox_paragraph_elements, _, doc_object = extract_docx_elements_and_objects(file_path)
                             if len(elements) != len(standard_paragraph_objects) or len(elements) != len(textbox_paragraph_elements):
                                 raise Exception("List lengths mismatched after re-extraction during rebuild.")
                    except Exception as reload_e:
                        raise Exception(f"DOCX object was invalid and failed to reload: {reload_e}")

                if not isinstance(doc_object, DocumentClass):
                    raise Exception("DOCX object not available for rebuilding.")

                rebuild_docx_with_lxml(
                    doc_object,
                    standard_paragraph_objects,
                    textbox_paragraph_elements,
                    None,
                    translated_elements,
                    out_file
                )
            elif original_format == "docx" and final_format == "pdf":
                if not isinstance(doc_object, DocumentClass):
                    print(f"⚠️ Warning: doc_object invalid before rebuild (->pdf). Attempting to reload {file_path}")
                    try:
                        doc_object = DocxDocument(file_path)
                        if not standard_paragraph_objects and not textbox_paragraph_elements:
                             print("  Re-extracting object references...")
                             _, standard_paragraph_objects, textbox_paragraph_elements, _, doc_object = extract_docx_elements_and_objects(file_path)
                             if len(elements) != len(standard_paragraph_objects) or len(elements) != len(textbox_paragraph_elements):
                                  raise Exception("List lengths mismatched after re-extraction during rebuild (->pdf).")
                    except Exception as reload_e:
                         raise Exception(f"DOCX object was invalid and failed to reload (->pdf): {reload_e}")

                if not isinstance(doc_object, DocumentClass):
                     raise Exception("DOCX object not available for rebuilding (->pdf).")

                rebuild_docx_with_lxml(
                    doc_object,
                    standard_paragraph_objects,
                    textbox_paragraph_elements,
                    None,
                    translated_elements,
                    temp_docx
                )
                created_temp_files.append(temp_docx)
                
                conversion_succeeded = False
                try:
                    convert_docx_to_pdf(temp_docx, out_file)
                    conversion_succeeded = os.path.exists(out_file) and os.path.getsize(out_file) > 0
                except Exception as conv_e:
                    print(f"⚠️ convert_docx_to_pdf() failed: {conv_e}")
                    traceback.print_exc()

                if not conversion_succeeded:
                    try:
                        from docx2pdf import convert as docx2pdf_convert
                        print("🔁 Falling back to docx2pdf.convert()...")
                        try:
                            docx2pdf_convert(temp_docx, out_file)
                        except TypeError:
                            docx2pdf_convert(temp_docx)
                        conversion_succeeded = os.path.exists(out_file) and os.path.getsize(out_file) > 0
                    except Exception as d2p_e:
                        print(f"⚠️ docx2pdf fallback failed: {d2p_e}")

                if not conversion_succeeded:
                    try:
                        if source_input_file and os.path.exists(source_input_file) and source_input_file.lower().endswith('.pdf'):
                            print("🔁 Last-resort: rebuilding translated content into original PDF using rebuild_pdf_in_place()...")
                            rebuild_pdf_in_place(source_input_file, translated_elements, out_file, target_lang)
                            conversion_succeeded = os.path.exists(out_file) and os.path.getsize(out_file) > 0
                    except Exception as pdf_rebuild_e:
                        print(f"⚠️ Last-resort PDF rebuild failed: {pdf_rebuild_e}")
                        traceback.print_exc()

                if not conversion_succeeded:
                    raise Exception("DOCX->PDF conversion failed (all methods tried).")

            if not os.path.exists(out_file) or os.path.getsize(out_file) == 0:
                 raise Exception(f"Output file '{out_file}' was not created or is empty after rebuild/conversion.")

            translated_files[target_lang] = os.path.basename(out_file)

        finally:
            for temp_file in created_temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        print(f"  Removed temporary file: {temp_file}")
                    except Exception as clean_e:
                        print(f"⚠️ Warning: Could not remove temporary file {temp_file}: {clean_e}")

        return translated_files

    except FileNotFoundError:
        print(f"⛔ ERROR: Input file not found at {file_path}")
        if task_id and tasks and task_id in tasks:
            tasks[task_id]["status"] = "error"
            tasks[task_id]["error_message"] = "Input file not found."
        return {}
    except ValueError as ve:
        print(f"⛔ ERROR: {ve}")
        if task_id and tasks and task_id in tasks:
            tasks[task_id]["status"] = "error"
            tasks[task_id]["error_message"] = f"Error: {ve}"
        return {}
    except Exception as e:
        print(f"❌ Unhandled error processing file {file_path}: {e}")
        traceback.print_exc()
        if task_id and tasks and task_id in tasks:
             tasks[task_id]["status"] = "error"
             tasks[task_id]["error_message"] = f"An unexpected processing error occurred. Please check logs."
        return {}

