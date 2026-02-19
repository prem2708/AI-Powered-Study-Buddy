from modules.llm_engine import get_client

SYSTEM_PROMPT = """You are StudyBuddy AI, a friendly, patient, and knowledgeable academic tutor.
Your job is to help students understand concepts, answer questions, clarify doubts, and make learning enjoyable.
Guidelines:
- Be encouraging and supportive
- Use simple language first, then add depth if asked
- Give examples and analogies when helpful
- Structure longer answers with markdown headers and bullet points
- If a student seems confused, offer to re-explain in a different way
- Keep responses focused and educational"""

def get_tutor_response(user_message: str, history: list[dict]) -> str:
    """
    Get a conversational response from the AI tutor.
    history: list of {"role": "user"/"assistant", "content": "..."}
    """
    client = get_client()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Include up to last 10 turns for context
    for msg in history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()
