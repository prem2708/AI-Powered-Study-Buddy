import json
import re
from modules.llm_engine import generate

def generate_quiz(content: str, num_questions: int = 5, quiz_type: str = "MCQ") -> list[dict]:
    """
    Generate quiz questions from a topic or notes.
    Returns a list of question dicts.
    MCQ: {type, question, options: [A,B,C,D], answer, explanation}
    True/False: {type, question, answer: True/False, explanation}
    Short Answer: {type, question, answer, explanation}
    """
    system = (
        "You are an expert quiz creator for students. Generate clear, educational quiz questions. "
        "You MUST respond with ONLY a valid JSON array, no extra text before or after."
    )

    if quiz_type == "MCQ":
        format_desc = (
            'a JSON array of objects, each with keys: '
            '"type" (always "mcq"), "question", "options" (array of 4 strings like ["A) ...", "B) ...", "C) ...", "D) ..."]), '
            '"answer" (the correct option letter, e.g. "A"), "explanation" (brief reason why)'
        )
    elif quiz_type == "True/False":
        format_desc = (
            'a JSON array of objects, each with keys: '
            '"type" (always "tf"), "question", '
            '"answer" (string "True" or "False"), "explanation" (brief reason why)'
        )
    else:  # Short Answer
        format_desc = (
            'a JSON array of objects, each with keys: '
            '"type" (always "sa"), "question", '
            '"answer" (a concise correct answer), "explanation" (brief elaboration)'
        )

    prompt = (
        f"Content/Topic: {content[:4000]}\n\n"
        f"Generate exactly {num_questions} {quiz_type} questions about this content.\n"
        f"Respond ONLY with {format_desc}.\n"
        "Ensure questions are varied, educational, and test real understanding."
    )

    raw = generate(prompt, system_prompt=system, temperature=0.6)

    # Extract JSON from response robustly
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: attempt full parse
    try:
        return json.loads(raw)
    except Exception:
        return []
