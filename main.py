import streamlit as st
import json
import os
import base64
import re
import streamlit.components.v1 as components

def clean_text_for_speech(text):
    """Remove markdown syntax for cleaner speech output."""
    if not text: return ""
    # Remove bold/italic markers (* or _)
    text = re.sub(r'[\*_]{1,3}', '', text)
    # Remove headers (#)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # Remove separators (--- or ===)
    text = re.sub(r'[-=]{3,}', '', text)
    # Remove links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove code blocks (content might be code, maybe skip or just read text?)
    # Reading code is annoying. Let's strip code blocks for now or keep them?
    # User said "unwanted part of text". Code is text.
    # But symbols like `def foo():` are fine.
    # Just remove the backticks.
    text = text.replace('`', '')
    return text.strip()

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudyBuddy AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Session State Init ───
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "explain_result" not in st.session_state: st.session_state.explain_result = ""
if "explain_topic" not in st.session_state: st.session_state.explain_topic = ""
if "summarize_result" not in st.session_state: st.session_state.summarize_result = ""
if "summarize_text" not in st.session_state: st.session_state.summarize_text = ""

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base Reset ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background: #0a0e1a;
    color: #e2e8f0;
}

/* ── Hide Streamlit Branding ── */
/* ── Hide Streamlit Branding ── */
#MainMenu, footer { visibility: hidden; }
/* header { visibility: hidden; } */

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1124 0%, #111827 100%);
    border-right: 1px solid rgba(99,102,241,0.2);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

/* ── Sidebar Navigation Styling ── */
/* Hide default radio buttons */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
    background: transparent;
    border-radius: 8px;
    margin-bottom: 0.2rem;
    transition: all 0.2s;
    cursor: pointer;
    font-weight: 500;
}
/* This is a bit tricky to target exact active state in pure CSS without hacks, 
   but we can style the hover state. */
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(99,102,241,0.15);
    color: #a78bfa !important;
}

/* ── Interactive Elements ── */
button { cursor: pointer !important; }
div[data-testid="stSelectbox"] > div > div { cursor: pointer !important; }
div[data-testid="stRadio"] label { cursor: pointer !important; }

/* ── Main Content ── */
.main .block-container { padding: 1.5rem 2rem 3rem; max-width: 960px; }

/* ── Hero Banner ── */
.hero-banner {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #1e3a5f 100%);
    border: 1px solid rgba(99,102,241,0.35);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    text-align: center;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 50% 0%, rgba(139,92,246,0.25) 0%, transparent 70%);
}
.hero-banner h1 { font-size: 2.8rem; font-weight: 800; margin: 0 0 0.5rem;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero-banner p { font-size: 1.1rem; color: #94a3b8; margin: 0; }

/* ── Feature Cards ── */
.feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1.5rem 0; }
.feature-card {
    background: rgba(30,27,75,0.5);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 16px;
    padding: 1.4rem;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}
.feature-card:hover { border-color: rgba(139,92,246,0.6); transform: translateY(-3px);
    box-shadow: 0 8px 32px rgba(99,102,241,0.2); }
.feature-card .icon { font-size: 2rem; margin-bottom: 0.6rem; }
.feature-card h3 { font-size: 1rem; font-weight: 600; color: #a78bfa; margin: 0 0 0.4rem; }
.feature-card p { font-size: 0.82rem; color: #94a3b8; margin: 0; line-height: 1.5; }

/* ── Section Headers ── */
.section-header {
    display: flex; align-items: center; gap: 0.75rem;
    margin: 1.5rem 0 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid rgba(99,102,241,0.3);
}
.section-header h2 { font-size: 1.5rem; font-weight: 700; margin: 0;
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

/* ── Result Container ── */
.result-box {
    background: rgba(15,23,42,0.8);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 16px;
    padding: 1.5rem;
    margin-top: 1rem;
    backdrop-filter: blur(10px);
}

/* ── Quiz Card ── */
.quiz-question {
    background: rgba(30,27,75,0.5);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.quiz-question .q-num { font-size: 0.78rem; font-weight: 600; color: #a78bfa;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; }
.quiz-question .q-text { font-size: 1rem; font-weight: 500; color: #e2e8f0; margin-bottom: 0.75rem; }

/* ── Score Bar ── */
.score-display {
    background: linear-gradient(135deg, #1e3a5f, #312e81);
    border: 1px solid rgba(99,102,241,0.4);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
}
.score-display h2 { font-size: 3rem; font-weight: 800; margin: 0;
    background: linear-gradient(90deg, #34d399, #60a5fa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.score-display p { font-size: 1rem; color: #94a3b8; margin: 0.5rem 0 0; }

/* ── Flashcard ── */
.flashcard-wrapper {
    perspective: 1200px;
    width: 100%; max-width: 640px;
    margin: 1.5rem auto;
    height: 260px;
    cursor: pointer;
}
.flashcard-inner {
    width: 100%; height: 100%;
    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    transform-style: preserve-3d;
    position: relative;
}
.flashcard-wrapper.flipped .flashcard-inner { transform: rotateY(180deg); }
.flashcard-face {
    position: absolute; inset: 0;
    border-radius: 20px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 2rem;
    backface-visibility: hidden;
    text-align: center;
}
.flashcard-front {
    background: linear-gradient(135deg, #1e1b4b, #312e81);
    border: 2px solid rgba(139,92,246,0.5);
    box-shadow: 0 8px 32px rgba(99,102,241,0.25);
}
.flashcard-back {
    background: linear-gradient(135deg, #0c3d2e, #1e3a5f);
    border: 2px solid rgba(52,211,153,0.5);
    box-shadow: 0 8px 32px rgba(52,211,153,0.15);
    transform: rotateY(180deg);
}
.flashcard-label { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; margin-bottom: 1rem; opacity: 0.7; }
.flashcard-front .flashcard-label { color: #a78bfa; }
.flashcard-back .flashcard-label { color: #34d399; }
.flashcard-content { font-size: 1.15rem; font-weight: 500; color: #e2e8f0; line-height: 1.6; }

/* ── Chat ── */
.chat-msg { display: flex; gap: 0.75rem; margin-bottom: 1rem; align-items: flex-start; }
.chat-msg.user { flex-direction: row-reverse; }
.chat-avatar {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}
.chat-msg.user .chat-avatar { background: linear-gradient(135deg, #7c3aed, #4f46e5); }
.chat-msg.assistant .chat-avatar { background: linear-gradient(135deg, #065f46, #1e3a5f); }
.chat-bubble {
    max-width: 80%;
    padding: 0.85rem 1.1rem;
    border-radius: 16px;
    font-size: 0.9rem;
    line-height: 1.6;
}
.chat-msg.user .chat-bubble {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: #f0f4ff;
    border-bottom-right-radius: 4px;
}
.chat-msg.assistant .chat-bubble {
    background: rgba(30,27,75,0.7);
    border: 1px solid rgba(99,102,241,0.25);
    color: #e2e8f0;
    border-bottom-left-radius: 4px;
}

/* ── Streamlit Widget Overrides ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: rgba(15,23,42,0.9) !important;
    border: 1px solid rgba(99,102,241,0.35) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(139,92,246,0.7) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.4rem !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
}
.stRadio > div { gap: 0.5rem; }
.stRadio > div > label {
    background: rgba(30,27,75,0.5);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 10px;
    padding: 0.4rem 0.9rem;
    transition: all 0.2s;
}
.stRadio > div > label:hover { border-color: rgba(139,92,246,0.5); }
.stSlider > div { color: #a78bfa; }
div[data-baseweb="notification"] { border-radius: 12px !important; }

/* ── Progress bar ── */
.stProgress > div > div > div { background: linear-gradient(90deg, #a78bfa, #60a5fa) !important; border-radius: 4px; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #a78bfa !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.4); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(139,92,246,0.7); }
</style>
""", unsafe_allow_html=True)

# ─── Imports after CSS ───────────────────────────────────────────────────────
from modules.explainer import explain_topic, LEVELS
from modules.summarizer import summarize_notes, extract_text_from_pdf
from modules.quiz_generator import generate_quiz
from modules.flashcard_generator import generate_flashcards
from modules.chat_tutor import get_tutor_response
from modules.llm_engine import transcribe_audio
from modules.chat_tutor import get_tutor_response
from modules.llm_engine import transcribe_audio
from modules.voice_engine import text_to_speech, speak, stop_audio

# ─── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0 1.5rem;'>
        <div style='font-size:2.8rem;'>🎓</div>
        <div style='font-size:1.3rem; font-weight:800;
            background: linear-gradient(90deg,#a78bfa,#60a5fa);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
            StudyBuddy AI
        </div>
        <div style='font-size:0.75rem; color:#64748b; margin-top:0.2rem;'>Powered by Llama 3.3 70B</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Navigation
    nav_options = [
        "🏠 Home",
        "💡 Explain",
        "📄 Summarize",
        "🎯 Quiz Me",
        "🃏 Flashcards",
        "💬 Chat Tutor"
    ]
    
    selected_page = st.radio(
        "Navigation",
        nav_options,
        label_visibility="collapsed",
        key="nav_radio"
    )

    # 🛑 Audio Control Logic
    if "last_page" not in st.session_state:
        st.session_state.last_page = selected_page
    
    if st.session_state.last_page != selected_page:
        stop_audio()
        st.session_state.last_page = selected_page

    st.markdown("---")
    audio_mode = st.radio(
        "Device", 
        ["🖥️ Server (Local)", "🌐 Browser (Remote)", "🔇 None"],
        index=1,
        key="audio_mode_selection",
        label_visibility="collapsed",
        help="Use 'Browser' if you cannot hear audio from the server."
    )

    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.72rem; color:#475569; text-align:center;'>
    Built with ❤️ using Streamlit + Groq<br>
    Free tier • No data stored
    </div>
    """, unsafe_allow_html=True)

# ─── Routing ────────────────────────────────────────────────────────────────
if selected_page == "🏠 Home":
    # ══════════════════════════════════════════════════════
    # 🏠 HOME
    # ══════════════════════════════════════════════════════
    st.markdown("""
    <div class='hero-banner'>
        <h1>🎓 StudyBuddy AI</h1>
        <p>Your personal AI-powered learning companion — understand, memorize, and master any subject.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='feature-grid'>
        <div class='feature-card'>
            <div class='icon'>💡</div>
            <h3>Explain Topics</h3>
            <p>Get crystal-clear explanations at your level — from ELI5 to advanced academic depth.</p>
        </div>
        <div class='feature-card'>
            <div class='icon'>📄</div>
            <h3>Summarize Notes</h3>
            <p>Paste your notes or upload a PDF. Get a concise summary, key points, and a glossary.</p>
        </div>
        <div class='feature-card'>
            <div class='icon'>🎯</div>
            <h3>Quiz Generator</h3>
            <p>Generate MCQs, True/False, or Short Answer questions on any topic. Track your score.</p>
        </div>
        <div class='feature-card'>
            <div class='icon'>🃏</div>
            <h3>Flashcards</h3>
            <p>Create interactive flip flashcards for rapid memorization of key concepts and terms.</p>
        </div>
        <div class='feature-card'>
            <div class='icon'>💬</div>
            <h3>Chat Tutor</h3>
            <p>Have a natural conversation with your AI tutor. Ask follow‑ups, get examples, clarify doubts.</p>
        </div>
        <div class='feature-card'>
            <div class='icon'>🚀</div>
            <h3>Free & Fast</h3>
            <p>Powered by Llama 3.3 70B via Groq's ultra-fast inference. Free API key at console.groq.com.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Capabilities")
    st.markdown("""
- ✅ 70B parameter model
- ✅ Multi-turn conversation
- ✅ PDF text extraction
- ✅ JSON-structured output
- ✅ Context-aware answers
- ✅ Live Voice Interaction (New!)
    """)

elif selected_page == "💡 Explain":
    # ══════════════════════════════════════════════════════
    # 💡 EXPLAIN TOPIC
    # ══════════════════════════════════════════════════════
    st.markdown("<div class='section-header'><span>💡</span><h2>Explain Any Topic</h2></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        # Use simple key for persistence automatically? 
        # Actually simplest way: just key="explain_topic_input". 
        # If widget is unmounted, value is lost? 
        # No, if keys are unique, Streamlit usually preserves. 
        # But if we navigate away, recent versions might clear.
        # Let's rely on standard st.session_state manual management for safety.
        
        def update_explain_topic():
            st.session_state.explain_topic = st.session_state.explain_topic_input
            
        topic_input = st.text_input("📚 Enter a topic", 
                                     value=st.session_state.explain_topic,
                                     placeholder="e.g. Quantum Entanglement, The French Revolution, Recursion in Python...",
                                     key="explain_topic_input",
                                     on_change=update_explain_topic)
    with col2:
        level_choice = st.selectbox("🎯 Complexity Level", list(LEVELS.keys()), key="explain_level")

    if st.button("✨ Explain It", key="btn_explain", use_container_width=True):
        if not topic_input.strip():
            st.warning("Please enter a topic first!")
        else:
            with st.spinner("🧠 Generating explanation..."):
                result = explain_topic(topic_input.strip(), level_choice)
                st.session_state.explain_result = result
                st.session_state.explain_topic = topic_input # Ensure saved
    
    # Display Result (Persistent)
    if st.session_state.explain_result:
        result = st.session_state.explain_result
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.markdown(result)
        st.markdown("</div>", unsafe_allow_html=True)
            
        # --- Export Options ---
        col_d, col_c = st.columns([1, 1])
        with col_d:
            st.download_button(
                "📥 Download Explanation", 
                result, 
                file_name=f"Explanation_{topic_input.replace(' ', '_')}.md",
                mime="text/markdown"
            )
        with col_c:
                 # Share Button (JS)
                 share_js = f"""
                 <script>
                 async function share() {{
                     const text = {json.dumps(result)};
                     try {{
                         await navigator.share({{ title: 'Explanation', text: text }});
                     }} catch (err) {{
                         console.log('Share failed', err);
                         navigator.clipboard.writeText(text);
                         alert('Copied to clipboard!');
                     }}
                 }}
                 </script>
                 <button onclick="share()" style="background:none; border:1px solid #4b5563; border-radius:5px; padding:5px 10px; color:white; font-size:1rem; cursor:pointer;" title="Share">📤 Share</button>
                 """
                 components.html(share_js, height=50)

elif selected_page == "📄 Summarize":
    # ══════════════════════════════════════════════════════
    # 📄 SUMMARIZE NOTES
    # ══════════════════════════════════════════════════════
    st.markdown("<div class='section-header'><span>📄</span><h2>Summarize Your Notes</h2></div>", unsafe_allow_html=True)

    input_mode = st.radio("Input Method", ["✏️ Type / Paste Text", "📎 Upload PDF"], horizontal=True, key="summ_mode")

    notes_text = ""
    if input_mode == "✏️ Type / Paste Text":
        def update_summarize_text():
            st.session_state.summarize_text = st.session_state.summ_text
            
        notes_text = st.text_area("📝 Paste your study notes here", height=220,
                                   value=st.session_state.summarize_text,
                                   placeholder="Paste your lecture notes, textbook excerpts, or any text you want summarized...",
                                   key="summ_text",
                                   on_change=update_summarize_text)
    else:
        uploaded = st.file_uploader("Upload a PDF file", type=["pdf"], key="summ_pdf")
        if uploaded:
            with st.spinner("📖 Extracting text from PDF..."):
                try:
                    notes_text = extract_text_from_pdf(uploaded)
                    st.success(f"✅ Extracted {len(notes_text):,} characters from PDF")
                    with st.expander("Preview extracted text"):
                        st.text(notes_text[:1000] + ("..." if len(notes_text) > 1000 else ""))
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")

    if st.button("📝 Summarize Notes", key="btn_summarize", use_container_width=True):
        if not notes_text.strip():
            st.warning("Please enter or upload some notes first!")
        elif len(notes_text.strip()) < 50:
            st.warning("Text is too short to summarize. Please provide more content.")
        else:
            with st.spinner("✍️ Summarizing your notes..."):
                result = summarize_notes(notes_text.strip())
                st.session_state.summarize_result = result
                # If generated from PDF, text area might be empty if we switch modes? 
                # But result persists.
    
    # Display Result (Persistent)
    if st.session_state.summarize_result:
        result = st.session_state.summarize_result
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.markdown(result)
        st.markdown("</div>", unsafe_allow_html=True)
            
        # --- Export Options ---
        col_d, col_c = st.columns([1, 1])
        with col_d:
            st.download_button(
                "📥 Download Summary", 
                result, 
                file_name="Summary.md",
                mime="text/markdown"
            )
        with col_c:
                 # Share Button (JS)
                 share_js = f"""
                 <script>
                 async function share() {{
                     const text = {json.dumps(result)};
                     try {{
                         await navigator.share({{ title: 'Summary', text: text }});
                     }} catch (err) {{
                         console.log('Share failed', err);
                         navigator.clipboard.writeText(text);
                         alert('Copied to clipboard!');
                     }}
                 }}
                 </script>
                 <button onclick="share()" style="background:none; border:1px solid #4b5563; border-radius:5px; padding:5px 10px; color:white; font-size:1rem; cursor:pointer;" title="Share">📤 Share</button>
                 """
                 components.html(share_js, height=50)

elif selected_page == "🎯 Quiz Me":
    # ══════════════════════════════════════════════════════
    # 🎯 QUIZ ME
    # ══════════════════════════════════════════════════════
    st.markdown("<div class='section-header'><span>🎯</span><h2>Quiz Generator</h2></div>", unsafe_allow_html=True)

    # Session state for quiz
    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = []
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        quiz_topic = st.text_area("📚 Topic or paste notes", height=100,
                                   placeholder="Enter a topic (e.g. 'World War 2') or paste your notes...",
                                   key="quiz_topic_input")
    with col2:
        quiz_num = st.slider("Questions", 3, 10, 5, key="quiz_num")
    with col3:
        quiz_type = st.selectbox("Type", ["MCQ", "True/False", "Short Answer"], key="quiz_type")

    if st.button("🎯 Generate Quiz", key="btn_generate_quiz", use_container_width=True):
        if not quiz_topic.strip():
            st.warning("Please enter a topic or notes!")
        else:
            with st.spinner("🎲 Crafting your quiz..."):
                questions = generate_quiz(quiz_topic.strip(), quiz_num, quiz_type)
            if questions:
                st.session_state.quiz_questions = questions
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.success(f"✅ Generated {len(questions)} questions!")
            else:
                st.error("Failed to generate quiz. Please try again with a different topic.")

    # Display quiz
    if st.session_state.quiz_questions and not st.session_state.quiz_submitted:
        st.markdown("---")
        questions = st.session_state.quiz_questions

        for i, q in enumerate(questions):
            qtype = q.get("type", "")
            question_text = q.get("question", f"Question {i+1}")

            st.markdown(f"""
            <div class='quiz-question'>
                <div class='q-num'>Question {i+1} of {len(questions)}</div>
                <div class='q-text'>{question_text}</div>
            </div>
            """, unsafe_allow_html=True)

            key = f"quiz_ans_{i}"
            if qtype == "mcq":
                options = q.get("options", [])
                answer = st.radio(f"Options for Q{i+1}", options, key=key, index=None, label_visibility="collapsed")
                if answer:
                    st.session_state.quiz_answers[i] = answer[0]  # first char = letter
            elif qtype == "tf":
                answer = st.radio(f"True/False for Q{i+1}", ["True", "False"], key=key, index=None, label_visibility="collapsed")
                if answer:
                    st.session_state.quiz_answers[i] = answer
            else:  # short answer
                answer = st.text_input("Answer", key=key, placeholder="Type your answer here...", label_visibility="collapsed")
                if answer:
                    st.session_state.quiz_answers[i] = answer

        if st.button("📊 Submit & See Results", key="btn_submit_quiz", use_container_width=True):
            st.session_state.quiz_submitted = True
            st.rerun()

    # Show results
    if st.session_state.quiz_submitted and st.session_state.quiz_questions:
        st.markdown("---")
        questions = st.session_state.quiz_questions
        answers = st.session_state.quiz_answers
        score = 0

        for i, q in enumerate(questions):
            qtype = q.get("type", "")
            correct = str(q.get("answer", "")).strip()
            user_ans = str(answers.get(i, "")).strip()
            explanation = q.get("explanation", "")

            is_correct = False
            if qtype == "mcq":
                is_correct = user_ans.upper() == correct.upper()
            elif qtype == "tf":
                is_correct = user_ans.lower() == correct.lower()
            else:
                is_correct = user_ans.lower().strip() == correct.lower().strip()

            if is_correct:
                score += 1

            icon = "✅" if is_correct else "❌"
            color = "#34d399" if is_correct else "#f87171"

            st.markdown(f"""
            <div style='background:rgba(15,23,42,0.7); border:1px solid {color}40;
                border-left: 4px solid {color}; border-radius:12px; padding:1rem; margin-bottom:0.75rem;'>
                <div style='font-weight:600; margin-bottom:0.4rem;'>{icon} Q{i+1}: {q.get("question","")}</div>
                <div style='font-size:0.85rem; color:{color};'>Correct Answer: <b>{correct}</b></div>
                {f"<div style='font-size:0.85rem; color:#94a3b8; margin-top:0.3rem;'>Your answer: {user_ans}</div>" if not is_correct else ""}
                {f"<div style='font-size:0.82rem; color:#64748b; margin-top:0.4rem; font-style:italic;'>{explanation}</div>" if explanation else ""}
            </div>
            """, unsafe_allow_html=True)

        pct = int(score / len(questions) * 100)
        grade = "🏆 Excellent!" if pct >= 80 else ("👍 Good Job!" if pct >= 60 else ("📚 Keep Studying!" if pct >= 40 else "💪 Don't Give Up!"))

        st.markdown(f"""
        <div class='score-display' style='margin-top:1.5rem;'>
            <h2>{score}/{len(questions)}</h2>
            <div style='font-size:1.5rem; color:#a78bfa;'>{pct}% • {grade}</div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(score / len(questions))

        if st.button("🔄 Try Again", key="btn_retry", use_container_width=True):
            st.session_state.quiz_submitted = False
            st.session_state.quiz_answers = {}
            st.rerun()

elif selected_page == "🃏 Flashcards":
    # ══════════════════════════════════════════════════════
    # 🃏 FLASHCARDS
    # ══════════════════════════════════════════════════════
    st.markdown("<div class='section-header'><span>🃏</span><h2>Flashcard Generator</h2></div>", unsafe_allow_html=True)

    if "flashcards" not in st.session_state:
        st.session_state.flashcards = []
    if "card_index" not in st.session_state:
        st.session_state.card_index = 0
    if "card_flipped" not in st.session_state:
        st.session_state.card_flipped = False

    col1, col2 = st.columns([4, 1])
    with col1:
        flash_topic = st.text_area("📚 Topic or paste notes", height=90,
                                    placeholder="Enter a topic or paste notes to generate flashcards...",
                                    key="flash_topic_input")
    with col2:
        flash_num = st.slider("Cards", 4, 20, 8, key="flash_num")

    if st.button("🃏 Generate Flashcards", key="btn_gen_flash", use_container_width=True):
        if not flash_topic.strip():
            st.warning("Please enter a topic!")
        else:
            with st.spinner("🎴 Creating flashcards..."):
                cards = generate_flashcards(flash_topic.strip(), flash_num)
            if cards:
                st.session_state.flashcards = cards
                st.session_state.card_index = 0
                st.session_state.card_flipped = False
                st.success(f"✅ Created {len(cards)} flashcards!")
            else:
                st.error("Failed to generate flashcards. Please try again.")

    # Display flashcards
    if st.session_state.flashcards:
        cards = st.session_state.flashcards
        idx = st.session_state.card_index
        card = cards[idx]
        flipped = st.session_state.card_flipped

        st.markdown("---")
        flip_class = "flipped" if flipped else ""

        st.markdown(f"""
        <div class='flashcard-wrapper {flip_class}' id='fc'>
            <div class='flashcard-inner'>
                <div class='flashcard-face flashcard-front'>
                    <div class='flashcard-label'>❓ Question / Term</div>
                    <div class='flashcard-content'>{card.get("front","")}</div>
                    <div style='font-size:0.72rem; color:#64748b; margin-top:1rem;'>Click button below to flip ↓</div>
                </div>
                <div class='flashcard-face flashcard-back'>
                    <div class='flashcard-label'>✅ Answer / Definition</div>
                    <div class='flashcard-content'>{card.get("back","")}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Controls
        col_prev, col_flip, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("◀ Prev", key="fc_prev", use_container_width=True, disabled=(idx == 0)):
                st.session_state.card_index = max(0, idx - 1)
                st.session_state.card_flipped = False
                st.rerun()
        with col_flip:
            flip_label = "👁️ Show Answer" if not flipped else "🔄 Show Question"
            if st.button(flip_label, key="fc_flip", use_container_width=True):
                st.session_state.card_flipped = not st.session_state.card_flipped
                st.rerun()
        with col_next:
            if st.button("Next ▶", key="fc_next", use_container_width=True, disabled=(idx == len(cards) - 1)):
                st.session_state.card_index = min(len(cards) - 1, idx + 1)
                st.session_state.card_flipped = False
                st.rerun()

        st.markdown(f"<div style='text-align:center; color:#64748b; font-size:0.85rem; margin-top:0.5rem;'>Card {idx+1} of {len(cards)}</div>", unsafe_allow_html=True)
        st.progress((idx + 1) / len(cards))

        # Card list toggle
        with st.expander("📋 View All Cards"):
            for j, c in enumerate(cards):
                st.markdown(f"""
                <div style='border:1px solid rgba(99,102,241,0.2); border-radius:10px;
                    padding:0.75rem 1rem; margin-bottom:0.5rem; font-size:0.88rem;'>
                    <b style='color:#a78bfa;'>#{j+1} {c.get("front","")}</b><br>
                    <span style='color:#94a3b8;'>{c.get("back","")}</span>
                </div>
                """, unsafe_allow_html=True)

elif selected_page == "💬 Chat Tutor":
    # ══════════════════════════════════════════════════════
    # 💬 CHAT TUTOR (With Voice)
    # ══════════════════════════════════════════════════════
    st.markdown("<div class='section-header'><span>💬</span><h2>Chat Tutor</h2></div>", unsafe_allow_html=True)

    # ─── Session State Init ───
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "explain_result" not in st.session_state:
        st.session_state.explain_result = ""
    if "explain_topic" not in st.session_state:
        st.session_state.explain_topic = ""
    if "summarize_result" not in st.session_state:
        st.session_state.summarize_result = ""
    if "summarize_text" not in st.session_state:
        st.session_state.summarize_text = ""
    if "latest_audio" not in st.session_state:
        st.session_state.latest_audio = None

    # Chat controls
    col_header, col_clear = st.columns([4, 1])
    with col_clear:
        if st.button("🗑️ Clear Chat", key="btn_clear_chat"):
            st.session_state.chat_history = []
            st.session_state.latest_audio = None
            st.rerun()

    # Welcome message when empty
    if not st.session_state.chat_history:
        st.markdown("""
        <div style='text-align:center; padding:2rem; color:#475569;'>
            <div style='font-size:3rem; margin-bottom:1rem;'>🤖</div>
            <div style='font-size:1rem; font-weight:600; color:#64748b;'>Hi there! I'm StudyBuddy AI</div>
            <div style='font-size:0.85rem; margin-top:0.4rem;'>
                Ask me anything — concepts, formulas, history, science, math, coding, or any subject!
            </div>
            <div style='margin-top:1.2rem; display:flex; gap:0.5rem; flex-wrap:wrap; justify-content:center;'>
                <span style='background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.3); border-radius:20px; padding:0.3rem 0.8rem; font-size:0.8rem; color:#94a3b8;'>💡 Explain gravity to a 10-year-old</span>
                <span style='background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.3); border-radius:20px; padding:0.3rem 0.8rem; font-size:0.8rem; color:#94a3b8;'>📐 How does calculus work?</span>
                <span style='background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.3); border-radius:20px; padding:0.3rem 0.8rem; font-size:0.8rem; color:#94a3b8;'>🧬 What is DNA replication?</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Chat history display
    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state.chat_history):
            role = msg["role"]
            content = msg["content"]
            audio_data = msg.get("audio")
            
            if role == "user":
                st.markdown(f"""
                <div class='chat-msg user'>
                    <div class='chat-avatar'>👤</div>
                    <div class='chat-bubble'>{content}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                with st.chat_message("assistant"):
                    # 🔊 Audio Toggle Button (Top of message)
                    # Show ONLY if this message was generated via Voice Input (or has audio data)
                    show_audio_btn = msg.get("is_voice", False) or msg.get("audio") is not None
                    
                    if show_audio_btn:
                        col_btn, _ = st.columns([2, 8])
                        with col_btn:
                             key_play = f"btn_play_{i}"
                             is_playing = (st.session_state.get("playing_msg_index") == i)
                             label = "⏸ Pause" if is_playing else "▶ Play"
                             
                             if st.button(label, key=key_play, use_container_width=True):
                                 if "None" in audio_mode:
                                      st.warning("Audio is disabled in Sidebar Settings.")
                                 else:
                                     # Stop any server audio first
                                     stop_audio()
                                     
                                     if is_playing:
                                         st.session_state.playing_msg_index = None
                                     else:
                                         st.session_state.playing_msg_index = i
                                         # Trigger server audio if in Server mode
                                         if "Server" in audio_mode:
                                             speak(clean_text_for_speech(content))
                                     st.rerun()

                    # Message Content
                    st.markdown(f"""
                    <div class='chat-msg assistant'>
                        <div class='chat-avatar'>🤖</div>
                        <div class='chat-bubble'>{content}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if audio_data:
                        # Logic: Autoplay if this is "playing" message AND we're in Browser mode
                        # (In Server mode, speak() handles it, so we don't autoplay st.audio to avoid echo)
                        should_autoplay = (is_playing and "Browser" in audio_mode)
                        
                        if should_autoplay:
                            # Convert to base64 for hidden HTML embedding (removes visible player UI)
                            try:
                                b64 = base64.b64encode(audio_data).decode()
                                md = f"""
                                <audio autoplay="true" style="display:none">
                                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                                </audio>
                                """
                                st.markdown(md, unsafe_allow_html=True)
                            except Exception as e:
                                print(f"Audio Embed Error: {e}")

    st.markdown("---")
    
    
    # 🎤 Voice Input
    if hasattr(st, "audio_input"):
        st.markdown("##### 🎤 Voice Mode")
        audio_val = st.audio_input("Record voice question", label_visibility="collapsed")
        
        if audio_val:
            # Check if this audio is new by comparing content
            audio_bytes = audio_val.read()
            # Simple hash check or state check to avoid re-transcribing same audio
            # But st.audio_input usually resets on rerun or holds value. 
            # We can check if it matches the last processed voice.
            # For simplicity, we process it if it's there. 
            pass 
            # Note: streamlit script reruns when audio is recorded.
    else:
        audio_val = None

    # ⌨️ Text Input
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_send = st.columns([5, 1])
        with col_input:
            user_msg = st.text_input("Your Message", placeholder="Type your question here...",
                                      key="chat_input", label_visibility="collapsed")
        with col_send:
            submitted = st.form_submit_button("Send 🚀", use_container_width=True)

    # Logic to handle input
    final_input = ""
    input_source = None  # "text" or "voice"
    
    # Prioritize Text if Submitted
    if submitted and user_msg.strip():
        final_input = user_msg.strip()
        input_source = "text"
    # Else check audio
    elif audio_val and len(audio_val.getvalue()) > 0:
        # Avoid reprocessing same audio loop
        # We need a way to detect if this specific audio has already been processed.
        # But st.audio_input retains value.
        # We can store a hash of audio bytes in session state.
        pass

    # We need to restructure slightly to handle the audio submission properly
    # Because st.audio_input triggers rerun immediately.
    
    if audio_val:
        # Transcribe
        with st.spinner("👂 Listening & Transcribing..."):
            # We only process if it's different from last time
            current_audio_hash = hash(audio_val.getvalue())
            if "last_audio_hash" not in st.session_state or st.session_state.last_audio_hash != current_audio_hash:
                st.session_state.last_audio_hash = current_audio_hash
                text_from_voice = transcribe_audio(audio_val)
                if text_from_voice.strip():
                     final_input = text_from_voice
                     input_source = "voice"
                else:
                    st.warning("Could not understand audio.")

    if final_input:
        st.session_state.chat_history.append({"role": "user", "content": final_input})
        
        with st.spinner("🤔 Thinking..."):
            reply_text = get_tutor_response(final_input, st.session_state.chat_history[:-1])
            
            # Generate TTS ONLY if input was voice
            audio_reply = None
            if input_source == "voice" and "None" not in audio_mode:
                
                if "Server" in audio_mode:
                    try:
                        stop_audio()
                        speak(clean_text_for_speech(reply_text))
                        # Mark as playing (index will be len(history) which is appended next)
                        st.session_state.playing_msg_index = len(st.session_state.chat_history)
                    except Exception as e:
                        print(f"Server TTS Error: {e}")

                # 2. Browser-side (if enabled or backup)
                # If "Browser" mode selected, we prioritize it and allow longer text
                limit = 5000 if "Browser" in audio_mode else 1500
                
                # If Server mode, browser audio is just backup/visual.
                # If Browser mode, it's essential.
                
                try:
                    if len(reply_text) < limit: 
                        # Use CLEANED text for TTS
                        audio_reply_bytes = text_to_speech(clean_text_for_speech(reply_text))
                        if audio_reply_bytes:
                            audio_reply = audio_reply_bytes.getvalue()
                except Exception as e:
                    print(f"Browser TTS Error: {e}")

        msg_obj = {"role": "assistant", "content": reply_text, "is_voice": (input_source == "voice")}
        if audio_reply:
             msg_obj["audio"] = audio_reply
        
        st.session_state.chat_history.append(msg_obj)
        st.rerun()

