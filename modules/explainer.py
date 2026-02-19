from modules.llm_engine import generate

LEVELS = {
    "🧒 ELI5 (Simple)": "Explain like I'm 5 years old. Use very simple language, short sentences, everyday analogies, and a friendly tone. Avoid jargon.",
    "📘 Standard": "Explain clearly for a high school or college student. Use proper terminology but keep it accessible.",
    "🔬 Advanced": "Give a comprehensive, in-depth explanation suitable for a graduate student or professional. Include technical details, mechanisms, and real-world applications.",
}

def explain_topic(topic: str, level: str) -> str:
    """Explain a topic at the given complexity level."""
    level_instruction = LEVELS.get(level, LEVELS["📘 Standard"])
    system = (
        "You are an expert educational tutor who excels at breaking down complex topics. "
        "Always structure your response with: a short intro, clear explanation, a real-world example, "
        "and a quick summary. Use markdown formatting with headers and bullet points."
    )
    prompt = (
        f"Topic: {topic}\n\n"
        f"Instruction: {level_instruction}\n\n"
        "Please explain this topic following the structure: "
        "## 📖 What is it?, ## 🔍 How it works, ## 🌍 Real-World Example, ## ✅ Quick Summary"
    )
    return generate(prompt, system_prompt=system)
