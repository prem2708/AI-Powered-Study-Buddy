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

# ─── Navigation Setup ───
NAV_OPTIONS = [
    "🏠 Home",
    "🧠 Explain",
    "📝 Summarize",
    "🎯 Quiz Me",
    "🗂️ Flashcards",
    "💬 Chat Tutor"
]
NAV_SLUGS = {
    "home": "🏠 Home",
    "explain": "🧠 Explain",
    "summarize": "📝 Summarize",
    "quiz": "🎯 Quiz Me",
    "flashcards": "🗂️ Flashcards",
    "chat": "💬 Chat Tutor",
}

try:
    qp = st.experimental_get_query_params()
    slug = (qp.get("page") or [None])[0]
    if slug in NAV_SLUGS:
        st.session_state.nav_radio = NAV_SLUGS[slug]
except Exception:
    pass

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root{
    --bg: #0b0d10;
    --surface: #12151b;
    --surface-2: #171c24;
    --border: rgba(148,163,184,0.18);
    --accent: #b6ff2b;
    --accent-2: #7dff3a;
    --muted: #a0a8b6;
    --text: #e6e9ef;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
}

#MainMenu, footer { visibility: hidden; }

[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding-top: 10px;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

[data-testid="stSidebar"] [data-testid="stRadio"] label{
    padding: 0.55rem 0.9rem;
    color: var(--muted);
    border-radius: 10px;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    transition: all 0.18s ease;
    font-weight: 600;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{
    background: rgba(182,255,43,0.12);
    color: var(--accent);
}
/* Active/selected state: Streamlit sometimes adds aria-checked on labels */
[data-testid="stSidebar"] [data-testid="stRadio"] label[aria-checked="true"],
[data-testid="stSidebar"] [data-testid="stRadio"] input:checked + label{
    background: linear-gradient(90deg, rgba(182,255,43,0.2), rgba(125,255,58,0.18));
    color: var(--text) !important;
    box-shadow: inset 0 0 0 1px rgba(182,255,43,0.35);
    border-radius: 10px;
}

button { cursor: pointer !important; }

.main .block-container { padding: 1.5rem 2.2rem 3rem; max-width: 1100px; }

.hero-banner {
    background: linear-gradient(135deg, rgba(182,255,43,0.08), rgba(125,255,58,0.06));
    border: 1px solid rgba(182,255,43,0.2);
    border-radius: 16px;
    padding: 2rem;
    text-align: left;
    margin-bottom: 1.6rem;
    box-shadow: 0 12px 28px rgba(2,6,23,0.45);
}
.hero-banner h1 { font-size: 2.2rem; font-weight: 800; margin: 0 0 0.5rem; color: var(--text); letter-spacing: 0.2px; }
.hero-banner p { font-size: 1rem; color: var(--muted); margin: 0 0 1rem; }
.hero-grid { display: grid; grid-template-columns: 1.3fr 1fr; gap: 1.6rem; align-items: center; }
.hero-actions { display:flex; gap:0.6rem; flex-wrap:wrap; margin-top:0.8rem; }
.hero-tag { display:inline-flex; align-items:center; gap:0.4rem; font-size:0.78rem; color: var(--text); background: rgba(182,255,43,0.12); border:1px solid rgba(182,255,43,0.3); padding:0.25rem 0.6rem; border-radius:999px; }
.hero-metrics { display:grid; grid-template-columns: repeat(3,1fr); gap:0.6rem; }
.metric-card { background: var(--surface); border:1px solid var(--border); border-radius:12px; padding:0.9rem; }
.metric-card .value { font-size:1.15rem; font-weight:700; color: var(--text); }
.metric-card .label { font-size:0.78rem; color: var(--muted); margin-top:0.2rem; }
.cta-button { background: linear-gradient(90deg, var(--accent), var(--accent-2)); color:#0b0d10; padding:0.6rem 1.1rem; border-radius:10px; font-weight:700; border:1px solid rgba(182,255,43,0.45); }
.ghost-button { background: transparent; color: var(--text); padding:0.55rem 1.05rem; border-radius:10px; border:1px solid var(--border); }

.feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1rem 0; }
.feature-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1rem; transition: all 0.18s; }
.feature-card:hover { transform: translateY(-3px); border-color: rgba(182,255,43,0.35); box-shadow: 0 14px 26px rgba(2,6,23,0.5); }
.feature-card h3 { font-size: 0.98rem; font-weight: 600; color: var(--text); }
.feature-card p { font-size: 0.9rem; color: var(--muted); }
.feature-card .tag { display:inline-flex; align-items:center; gap:0.4rem; font-size:0.72rem; color: var(--muted); border:1px solid var(--border); padding:0.2rem 0.5rem; border-radius:999px; }

.home-section { margin-top: 1.4rem; }
.home-title { font-size:1.2rem; font-weight:700; color: var(--text); margin-bottom:0.6rem; }
.home-subtitle { font-size:0.9rem; color: var(--muted); margin-bottom:0.9rem; }
.workflow { display:grid; grid-template-columns: repeat(3,1fr); gap:1rem; }
.workflow-step { background: var(--surface-2); border:1px solid var(--border); border-radius:12px; padding:1rem; }
.workflow-step .step { font-size:0.75rem; color: var(--muted); }
.workflow-step .title { font-size:0.95rem; font-weight:600; color: var(--text); margin-top:0.25rem; }
.workflow-step .desc { font-size:0.85rem; color: var(--muted); margin-top:0.35rem; }

.home-banner { background: var(--surface); border:1px solid var(--border); border-radius:14px; padding:1rem 1.2rem; display:flex; justify-content:space-between; align-items:center; gap:1rem; }
.home-banner .note { font-size:0.9rem; color: var(--muted); }

.section-header { display:flex; align-items:center; gap:0.6rem; margin:1rem 0 0.6rem; padding-bottom:0.5rem; border-bottom:1px solid var(--border); }
.section-header h2{ font-size:1.28rem; font-weight:700; margin:0; color:var(--text); }

.result-box { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.2rem; margin-top: 1rem; }

.quiz-question { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; margin-bottom:0.9rem; }

.flashcard-wrapper { max-width: 680px; height: 240px; margin: 1rem auto; }

.chat-msg { display:flex; align-items:flex-start; gap:0.6rem; margin-bottom:0.75rem; }
.chat-avatar { width: 32px; height: 32px; display:flex; align-items:center; justify-content:center; border-radius: 50%; background: rgba(182,255,43,0.12); color: var(--accent); font-size: 0.9rem; }
.chat-bubble { padding: 0.75rem 1rem; border-radius: 12px; background: var(--surface-2); border: 1px solid var(--border); }
.chat-msg.user .chat-bubble { background: rgba(182,255,43,0.14); border-color: rgba(182,255,43,0.35); }

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; color: var(--text) !important; }
.stButton > button { background: linear-gradient(90deg, var(--accent), var(--accent-2)) !important; color: #0b0d10 !important; border-radius: 10px !important; padding: 0.56rem 1.1rem !important; font-weight:700 !important; border: 1px solid rgba(182,255,43,0.45) !important; }
.stButton > button:hover{ transform: translateY(-1px) !important; box-shadow: 0 10px 24px rgba(182,255,43,0.25) !important; }

.stProgress > div > div > div { background: var(--accent) !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }

@media (max-width: 900px){
  .hero-grid{ grid-template-columns: 1fr; }
  .feature-grid{ grid-template-columns: repeat(2,1fr); }
  .workflow{ grid-template-columns: 1fr; }
  .hero-metrics{ grid-template-columns: repeat(3,1fr); }
  .main .block-container{ padding-left: 1rem; padding-right:1rem; }
}
@media (max-width: 600px){
  .feature-grid{ grid-template-columns: 1fr; }
  .hero-banner h1{ font-size:1.6rem; }
  .hero-metrics{ grid-template-columns: 1fr; }
  .home-banner{ flex-direction: column; align-items:flex-start; }
}

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
        <div style='font-size:1.35rem; font-weight:800; color:#0f172a; letter-spacing:0.2px;'>
            StudyBuddy
        </div>
        <div style='font-size:0.75rem; color:#64748b; margin-top:0.2rem;'>AI learning assistant</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Navigation
    selected_page = st.radio(
        "Navigation",
        NAV_OPTIONS,
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
        <div class='hero-grid'>
            <div>
                <div class='hero-tag'>⚡ Fast, focused study sessions</div>
                <h1>StudyBuddy</h1>
                <p>Understand faster with concise explanations, smart summaries, and targeted practice built for daily learning.</p>
                <div class='home-subtitle'>Built for focused study sessions with clear outputs you can save and revisit.</div>
            </div>
            <div class='hero-metrics'>
                <div class='metric-card'>
                    <div class='value'>5 Modes</div>
                    <div class='label'>Explain, summarize, quiz, flashcards, chat</div>
                </div>
                <div class='metric-card'>
                    <div class='value'>PDF Ready</div>
                    <div class='label'>Extract notes instantly</div>
                </div>
                <div class='metric-card'>
                    <div class='value'>Voice</div>
                    <div class='label'>Talk and listen hands‑free</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='feature-grid'>
        <div class='feature-card'>
            <div class='tag'>💡 Explain</div>
            <h3>Clear explanations</h3>
            <p>Pick your level and get structured, easy‑to‑follow answers.</p>
        </div>
        <div class='feature-card'>
            <div class='tag'>📝 Summarize</div>
            <h3>Shorter notes</h3>
            <p>Turn long notes or PDFs into concise, actionable summaries.</p>
        </div>
        <div class='feature-card'>
            <div class='tag'>🎯 Quiz</div>
            <h3>Targeted practice</h3>
            <p>Generate quizzes and measure how well you understand topics.</p>
        </div>
        <div class='feature-card'>
            <div class='tag'>🗂️ Flashcards</div>
            <h3>Active recall</h3>
            <p>Memorize key terms with fast, flip‑style cards.</p>
        </div>
        <div class='feature-card'>
            <div class='tag'>💬 Chat</div>
            <h3>Guided learning</h3>
            <p>Ask follow‑ups and get step‑by‑step tutoring.</p>
        </div>
        <div class='feature-card'>
            <div class='tag'>🔊 Voice</div>
            <h3>Hands‑free mode</h3>
            <p>Speak your question and listen to the response.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='home-section'>", unsafe_allow_html=True)
    st.markdown("<div class='home-title'>How it works</div>", unsafe_allow_html=True)
    st.markdown("<div class='home-subtitle'>A simple flow designed for quick study sessions.</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='workflow'>
        <div class='workflow-step'>
            <div class='step'>Step 1</div>
            <div class='title'>Drop your topic or notes</div>
            <div class='desc'>Type a question, paste notes, or upload a PDF.</div>
        </div>
        <div class='workflow-step'>
            <div class='step'>Step 2</div>
            <div class='title'>Choose a mode</div>
            <div class='desc'>Explain, summarize, quiz, flashcards, or chat.</div>
        </div>
        <div class='workflow-step'>
            <div class='step'>Step 3</div>
            <div class='title'>Review and retain</div>
            <div class='desc'>Save results, practice, and come back anytime.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='home-section'>", unsafe_allow_html=True)
    st.markdown("<div class='home-title'>Why students use StudyBuddy</div>", unsafe_allow_html=True)
    st.markdown("<div class='home-subtitle'>Designed to reduce study friction and keep you consistent.</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='feature-grid'>
        <div class='feature-card'>
            <div class='tag'>✅ Clarity</div>
            <h3>Structured answers</h3>
            <p>Responses are organized with headings, key points, and concise explanations.</p>
        </div>
        <div class='feature-card'>
            <div class='tag'>⚡ Speed</div>
            <h3>Quick feedback</h3>
            <p>Get results fast so you can move to practice without delays.</p>
        </div>
        <div class='feature-card'>
            <div class='tag'>🔁 Consistency</div>
            <h3>Repeatable workflow</h3>
            <p>Use the same steps across topics to build steady habits.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='home-section'>", unsafe_allow_html=True)
    st.markdown("""
    <div class='home-banner'>
        <div>
            <div class='home-title'>Study smarter today</div>
            <div class='note'>Switch between modes without losing your progress. Save results and revisit anytime.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='home-section'>", unsafe_allow_html=True)
    st.markdown("<div class='home-title'>Getting the best results</div>", unsafe_allow_html=True)
    st.markdown("<div class='home-subtitle'>A few quick tips to improve quality and accuracy.</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='workflow'>
        <div class='workflow-step'>
            <div class='step'>Tip 1</div>
            <div class='title'>Be specific</div>
            <div class='desc'>Include the topic scope, level, and any constraints.</div>
        </div>
        <div class='workflow-step'>
            <div class='step'>Tip 2</div>
            <div class='title'>Use short chunks</div>
            <div class='desc'>Split large notes for clearer summaries and quizzes.</div>
        </div>
        <div class='workflow-step'>
            <div class='step'>Tip 3</div>
            <div class='title'>Review and repeat</div>
            <div class='desc'>Revisit flashcards or quizzes for stronger retention.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif selected_page == "🧠 Explain":
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

elif selected_page == "📝 Summarize":
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

elif selected_page == "🗂️ Flashcards":
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

