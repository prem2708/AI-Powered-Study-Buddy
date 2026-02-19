import json
import re
from modules.llm_engine import generate

def generate_flashcards(content: str, num_cards: int = 8) -> list[dict]:
    """
    Generate flashcards from a topic or notes.
    Returns a list of {front: str, back: str} dicts.
    """
    system = (
        "You are an expert educational flashcard creator. "
        "Create concise, clear question-answer pairs that aid memorization. "
        "You MUST respond with ONLY a valid JSON array, no extra text."
    )
    prompt = (
        f"Content/Topic: {content[:4000]}\n\n"
        f"Generate exactly {num_cards} flashcards.\n"
        'Respond ONLY with a JSON array of objects with keys "front" (question/term) and "back" (answer/definition).\n'
        "Make the fronts concise questions or terms, and the backs clear, memorable answers. "
        "Vary between definitions, key facts, formulas, and conceptual questions."
    )

    raw = generate(prompt, system_prompt=system, temperature=0.5)

    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(raw)
    except Exception:
        return []
