import time
import re
from src.config import llm
from copy import deepcopy

# Define the batch size
BATCH_SIZE = 15

# --- NEW: Robust patterns to protect technical content ---
# We define them from most-specific to least-specific to avoid conflicts.
# e.g., We must find ```...``` before `...`, and $$...$$ before $...$
PROTECTION_PATTERNS = [
    # 1. Fenced Code Blocks (```...```)
    {"name": "CODE_BLOCK", "pattern": re.compile(r"(```.*?```)", re.DOTALL)},
    # 2. Display Math ($$...$$)
    {"name": "MATH_DISP", "pattern": re.compile(r"(\$\$.*?\$\$)", re.DOTALL)},
    # 3. Inline Code (`...`)
    {"name": "CODE_INLINE", "pattern": re.compile(r"(`.*?`)")},
    # 4. Inline Math ($...$)
    {"name": "MATH_INLINE", "pattern": re.compile(r"(\$.*?\$)", re.DOTALL)},
    # 5. Common Symbols (©, ®, ™)
    {"name": "SYM", "pattern": re.compile(r"([©®™])")},
]

def _get_system_prompt(target_lang):
    """
    Creates a detailed system prompt for high-accuracy technical document translation.
    This prompt instructs the AI on how to handle placeholders for code and math.
    """
    return f"""
    You are an expert technical document translator. Your task is to translate a batch of text elements from English to {target_lang}.

    RULES:
    1.  **Translate Content:** Accurately translate the text.
    2.  **Handle Placeholders:** The text contains placeholders for technical content.
        * Placeholders look like `[CODE_BLOCK_1]`, `[MATH_INLINE_2]`, `[SYM_0]`, etc.
        * These placeholders represent code, equations, or symbols that MUST NOT be translated or altered.
        * You MUST preserve these placeholders *exactly as-is* in their original position in the translated text.
        * Example Input: "This is `[CODE_INLINE_0]` and `[MATH_INLINE_1]`."
        * Example Output (to French): "Ceci est `[CODE_INLINE_0]` et `[MATH_INLINE_1]`."
    3.  **Handle Headings:** You SHOULD translate common structural headings (e.g., "Introduction", "Conclusion", "Appendix"). You SHOULD NOT translate proper nouns or specific titles (e.g., "A Study of Finches").
    4.  **Preserve Formatting:** Maintain all original line breaks and paragraph structure within each element.
    5.  **Output Format:** The user will provide elements separated by "|||". You MUST provide *only* the translated text for each element, separated by the same "|||" separator. The number of output elements must exactly match the input.
    """

def _protect_content(text):
    """
    Iteratively finds and replaces all technical content (code, math)
    with placeholders.
    
    Returns:
        - protected_text (str): The text with placeholders.
        - restoration_map (dict): A map of {placeholder: original_content}
    """
    restoration_map = {}
    counters = {p["name"]: 0 for p in PROTECTION_PATTERNS}
    
    protected_text = text

    for item in PROTECTION_PATTERNS:
        name = item["name"]
        pattern = item["pattern"]
        
        # We need a function to handle the replacement so we can increment the counter
        def replacer(match):
            original_content = match.group(1)
            placeholder_key = f"[{name}_{counters[name]}]"
            counters[name] += 1
            
            restoration_map[placeholder_key] = original_content
            return placeholder_key

        protected_text = pattern.sub(replacer, protected_text)
        
    return protected_text, restoration_map

def _restore_content(protected_text, restoration_map):
    """
    Restores the original technical content from the placeholders.
    """
    if not restoration_map:
        return protected_text

    restored_text = protected_text
    try:
        # Restore in reverse order of placeholder keys (most nested first)
        # This isn't strictly necessary with our current regex, but it's safer.
        for placeholder, original in sorted(restoration_map.items(), key=lambda x: x[0], reverse=True):
            restored_text = restored_text.replace(placeholder, original)
    except Exception as e:
        print(f"⚠️ Warning: Content restoration failed. {e}")
        return protected_text # Return text with placeholders if restore fails
    
    return restored_text


def _translate_batch(batch, target_lang, system_prompt):
    """
    Translates a single batch of text elements using the provided system prompt.
    """
    # 1. Prepare batch and protect content
    original_texts = []
    restoration_maps = []

    for el in batch:
        text = el.get("text", "")
        
        # Protect all technical content (code, math, etc.)
        protected_text, restoration_map = _protect_content(text)

        original_texts.append(protected_text)
        restoration_maps..append(restoration_map)

    # 2. Combine batch into a single prompt string
    prompt_string = "|||".join(original_texts)
    
    # 3. Create the full prompt with the system message
    full_prompt = f"{system_prompt}\n\nTranslate the following elements to {target_lang}. Maintain the '|||' separator.\n\nInput:\n{prompt_string}\n\nOutput:"
    
    # 4. Call the LLM
    try:
        response = llm.invoke(full_prompt)
        translated_content = response.content if hasattr(response, 'content') else str(response)
        translated_batch_texts = translated_content.strip().split("|||")
    except Exception as e:
        print(f"❌ LLM invocation failed: {e}")
        return None # Signal failure

    # 5. Verify batch length
    if len(translated_batch_texts) != len(batch):
        print(f"⚠️ Warning: Mismatch in translated batch length. Got {len(translated_batch_texts)}, expected {len(batch)}. Falling back.")
        return None # Signal failure

    # 6. Restore placeholders and create new elements
    restored_elements = []
    for i, el in enumerate(batch):
        translated_txt = translated_batch_texts[i]
        restoration_map = restoration_maps[i]

        # Restore all protected content
        restored = _restore_content(translated_txt, restoration_map)

        new_el = deepcopy(el)
        new_el["text"] = restored.strip()
        restored_elements.append(new_el)
    
    return restored_elements


def translate_elements(elements, target_lang, task_id=None, tasks=None):
    """
    Translates a list of document elements in batches, showing progress.
    """
    print(f"--- Starting translation of {len(elements)} elements to {target_lang} ---")
    translated_elements = []
    total_elements = len(elements)
    
    # --- NEW: Get the robust system prompt once ---
    system_prompt = _get_system_prompt(target_lang)

    for i in range(0, total_elements, BATCH_SIZE):
        batch = elements[i:i + BATCH_SIZE]
        
        # Update progress
        progress = (i / total_elements) * 100
        if task_id and tasks:
            tasks[task_id]["progress"] = 30 + (progress * 0.6) # Translation is 30% -> 90%
        print(f"  Translating batch {i // BATCH_SIZE + 1}/{(total_elements + BATCH_SIZE - 1) // BATCH_SIZE}...")

        try:
            restored_batch = _translate_batch(batch, target_lang, system_prompt)
            
            if restored_batch is None:
                # If translation failed, append original batch to avoid data loss
                print("  Batch translation failed, appending original elements.")
                translated_elements.extend(deepcopy(batch))
            else:
                translated_elements.extend(restored_batch)

        except Exception as e:
            print(f"❌ Error during batch translation to {target_lang}: {e}")
            # Append original batch on error
            translated_elements.extend(deepcopy(batch))
        
        # --- FIX: Increase sleep time to 3 seconds to avoid API rate limits ---
        time.sleep(3) # To respect API rate limits

    print("--- Translation complete ---")
    return translated_elements
