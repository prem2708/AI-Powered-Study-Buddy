import io
import PyPDF2
from modules.llm_engine import generate

def extract_text_from_pdf(uploaded_file) -> str:
    """Extract raw text from an uploaded PDF file."""
    try:
        # Reset file pointer to beginning to avoid empty reads on reruns
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
            
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        return f"Error reading PDF: {e}"

def summarize_notes(text: str) -> str:
    """Summarize study notes and extract key points and terms."""
    system = (
        "You are an expert academic summarizer. Your job is to condense study material "
        "into clear, structured summaries that help students retain information efficiently. "
        "Always use markdown formatting."
    )
    prompt = (
        f"Here are the study notes to summarize:\n\n---\n{text[:6000]}\n---\n\n"
        "Please provide:\n"
        "## 📝 Summary\n(A concise 3-5 sentence overview)\n\n"
        "## 🔑 Key Points\n(Bullet list of the most important takeaways)\n\n"
        "## 📚 Important Terms & Definitions\n(A brief glossary of key terms)\n\n"
        "## 💡 Study Tips\n(2-3 actionable tips for mastering this material)"
    )
    return generate(prompt, system_prompt=system, temperature=0.4)
