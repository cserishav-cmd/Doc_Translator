import re
from src import translator
import src.config as config


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def invoke(self, prompt: str):
        # Extract the TEXT TO TRANSLATE block between the last pair of '---' markers
        parts = prompt.rsplit('---', 2)
        if len(parts) >= 2:
            to_translate = parts[-2]
        else:
            # Fallback: return prompt unchanged
            to_translate = prompt

        # Simulate translation: replace the English word 'Hello' with a Hindi equivalent
        translated = to_translate.replace('Hello', 'नमस्ते')

        # Return the translated content (preserving any placeholders like [MATH_0_0])
        return FakeResponse(translated)


def test_math_placeholders_preserved(monkeypatch):
    # Patch the global llm to our fake
    monkeypatch.setattr(config, 'llm', FakeLLM())

    # Create a batch with inline math and display math plus normal text
    elements = [
        {"text": "Calculate $E=mc^2$ and Hello", "is_heading": False},
        {"text": "Display math: $$\int_0^1 x^2 dx$$ followed by Hello", "is_heading": False},
    ]

    translated = translator.translate_elements(elements, target_lang='hindi')

    # Ensure we got the right number of elements back
    assert len(translated) == 2

    # Check that math expressions are preserved exactly
    assert '$E=mc^2$' in translated[0]['text']
    assert '$$\int_0^1 x^2 dx$$' in translated[1]['text']

    # Check that non-math text got 'translated' by our FakeLLM
    assert 'नमस्ते' in translated[0]['text']
    assert 'नमस्ते' in translated[1]['text']
