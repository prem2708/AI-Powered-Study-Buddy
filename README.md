# StudyBuddy AI

> A Streamlit-based learning assistant that explains topics, summarizes notes, generates quizzes and flashcards, provides a chat-style tutor, and supports text-to-speech and audio transcription via Groq APIs.

---

## Features
- Explain topics at multiple levels (ELI5, Standard, Advanced)
- Summarize notes and extract text from PDFs
- Generate quizzes (MCQ, True/False, Short Answer)
- Generate flashcards (JSON output of front/back pairs)
- Chat-style tutor with conversation history
- Text-to-speech (server/browser) and audio transcription

## Quick start
1. Clone the project or open the workspace.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Add your Groq API key to a `.env` file at the project root:

```
GROQ_API_KEY=your_real_groq_api_key_here
```

4. Run the app with Streamlit:

```powershell
streamlit run main.py
```

Open the URL printed by Streamlit (usually http://localhost:8501).

## Environment & Config
- The app uses the Groq client. Set `GROQ_API_KEY` in `.env` or Streamlit secrets.
- Optional TTS/playback libraries: `pyttsx3`, `pydub`, `gTTS`. If missing, the voice features will fall back or be limited.

## Project layout
- [main.py](main.py): Streamlit app and UI routing (home, explain, summarize, quiz, flashcards, chat).
- [requirements.txt](requirements.txt): Python dependencies.
- [test_audio.py](test_audio.py): Local audio diagnostic script to check TTS/playback.
- `modules/` folder: core backend helpers and LLM wrappers.

### Modules (overview)
- [modules/llm_engine.py](modules/llm_engine.py)
  - Initializes the Groq client via `get_client()` and exposes `generate()` for chat/completions and `transcribe_audio()` for audio transcription.
  - Important: validates `GROQ_API_KEY` and stops the app with a helpful Streamlit message if missing.

- [modules/explainer.py](modules/explainer.py)
  - Exposes `explain_topic(topic, level)` and a `LEVELS` preset mapping.
  - Uses `generate()` from the LLM engine to request a structured explanation (intro, how it works, example, summary).

- [modules/summarizer.py](modules/summarizer.py)
  - `extract_text_from_pdf(uploaded_file)`: uses `PyPDF2` to extract text from uploaded PDF files.
  - `summarize_notes(text)`: asks the LLM to return a markdown-formatted summary, key points, glossary, and study tips.

- [modules/quiz_generator.py](modules/quiz_generator.py)
  - `generate_quiz(content, num_questions, quiz_type)`: builds prompts for MCQ / True-False / Short Answer quizzes and parses JSON responses.
  - Returns arrays of question dictionaries (the function includes robust JSON extraction fallback logic).

- [modules/flashcard_generator.py](modules/flashcard_generator.py)
  - `generate_flashcards(content, num_cards)`: prompts the LLM to return a JSON array of `{front, back}` flashcards for memorization.

- [modules/chat_tutor.py](modules/chat_tutor.py)
  - `get_tutor_response(user_message, history)`: wraps a conversational LLM call using a `SYSTEM_PROMPT` tuned for a helpful tutor persona.

- [modules/voice_engine.py](modules/voice_engine.py)
  - Provides TTS helpers: `text_to_speech()`, `speak()`, `stop_audio()`.
  - Uses `pyttsx3` (preferred) with a background worker thread and falls back to `gTTS` + `pydub` when needed.
  - Includes robust thread/queue and reinitialization behavior for Windows environments.

## Usage notes
- The UI is implemented in `main.py` and imports the modules above. The app includes multiple pages accessible from the sidebar: Home, Explain, Summarize, Quiz, Flashcards, Chat Tutor.
- Audio mode: the sidebar offers `Server (Local)`, `Browser (Remote)`, or `None`. Server-side playback requires working TTS/playback libraries; browser playback uses `text_to_speech()` output and `st.audio`.

## Running audio diagnostics
Use `test_audio.py` to quickly verify local TTS/playback capability (pyttsx3, pydub/gTTS). Run:

```powershell
python test_audio.py
```

Review output for missing libraries or playback errors.

## Troubleshooting
- If you see a Groq API error, confirm `GROQ_API_KEY` is set and valid.
- If TTS playback fails on Windows, ensure `pyttsx3` and `pywin32` are installed. If using `pydub`, ensure `ffmpeg` is available on PATH.

## Tests & Development
- There are no automated unit tests included. To validate audio locally, use `test_audio.py`.

## Contributing
- Suggestions, bug reports, or improvements are welcome. Typical contributions:
  1. Open an issue describing the change.
 2. Submit a PR with a clear description and small, focused commits.

## License
This repository does not include a license file. If you want to make this project open source, consider adding an `MIT` or similar license.

---

If you'd like, I can also:
- add a `README` badge and a short `LICENSE` file, or
- commit the change and run a quick local smoke-check (if you want me to run tests here).
