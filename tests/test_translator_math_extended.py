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

        # Simulate translation: replace the English word 'Example' with 'उदाहरण'
        translated = to_translate.replace('Example', 'उदाहरण')

        # Return the translated content (preserving any placeholders like [MATH_0_0])
        return FakeResponse(translated)


def test_extended_math_and_symbols(monkeypatch):
    # Patch the global llm to our fake
    monkeypatch.setattr(config, 'llm', FakeLLM())

    elements = [
        {"text": "Inline math with parentheses: $f(x)=\alpha x + \beta$ and Example", "is_heading": False},
        {"text": "Display math with brackets: \\[ E = mc^2 \\] then Example", "is_heading": False},
        {"text": "Equation environment: \\begin{equation}a^2+b^2=c^2\\end{equation} Example", "is_heading": False},
        {"text": "Symbols: α β ≤ ≥ ± Example", "is_heading": False},
    ]

    translated = translator.translate_elements(elements, target_lang='hindi')

    assert len(translated) == 4

    # Math and environment blocks preserved
    assert '$f(x)=\alpha x + \beta$' in translated[0]['text']
    assert '\\[ E = mc^2 \\]' in translated[1]['text']
    assert '\\begin{equation}a^2+b^2=c^2\\end{equation}' in translated[2]['text']

    # Symbols preserved
    assert 'α' in translated[3]['text']
    assert 'β' in translated[3]['text']
    assert '≤' in translated[3]['text']
    assert '≥' in translated[3]['text']
    assert '±' in translated[3]['text']

    # Non-math text translated by fake LLM
    assert 'उदाहरण' in translated[0]['text']
    assert 'उदाहरण' in translated[1]['text']