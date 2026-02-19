import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_client():
    """Initialize and return a Groq client."""
    api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        st.error("⚠️ GROQ_API_KEY is not set. Please add your key to the `.env` file.")
        st.stop()
    return Groq(api_key=api_key)

def generate(prompt: str, system_prompt: str = "You are a helpful AI study assistant.", temperature: float = 0.7) -> str:
    """Send a prompt to the LLM and return the response text."""
    client = get_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=2048,
    )
    return response.choices[0].message.content.strip()

def transcribe_audio(audio_file) -> str:
    """Transcribe audio file-like object using Groq Whisper."""
    client = get_client()
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_file), # Filename is required
            model="whisper-large-v3",
            response_format="text"
        )
        return transcription
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return ""
