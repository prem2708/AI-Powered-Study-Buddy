"""
database.py — Supabase data layer for StudyBuddy
Handles all CRUD operations: notes, quiz results, flashcard sets, chat history.
"""

import os
import json
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


@st.cache_resource
def get_supabase() -> Client:
    """Initialize and return a cached Supabase client."""
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
    return create_client(url, key)


# ─── Authentication ─────────────────────────────────────────────────────────

def auth_sign_up(email: str, password: str, name: str) -> dict:
    """Sign up a new user via Supabase Auth."""
    sb = get_supabase()
    res = sb.auth.sign_up({"email": email, "password": password, "options": {"data": {"full_name": name}}})
    return res

def auth_sign_in(email: str, password: str) -> dict:
    """Sign in an existing user via Supabase Auth."""
    sb = get_supabase()
    res = sb.auth.sign_in_with_password({"email": email, "password": password})
    return res

def auth_sign_out():
    """Sign out the current user via Supabase Auth."""
    sb = get_supabase()
    sb.auth.sign_out()

def restore_session(access_token: str, refresh_token: str) -> dict | None:
    """Restore a Supabase session using saved tokens."""
    try:
        sb = get_supabase()
        res = sb.auth.set_session(access_token, refresh_token)
        return res
    except Exception as e:
        # Ignore errors if token is expired/invalid
        return None

# ─── User Profiles ──────────────────────────────────────────────────────────

def upsert_user_profile(user_id: str, email: str = "", name: str = "") -> dict | None:
    """Create or update user profile synced from Supabase Auth."""
    try:
        sb = get_supabase()
        result = sb.table("user_profiles").upsert(
            {"user_id": user_id, "email": email, "name": name},
            on_conflict="user_id"
        ).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.warning(f"⚠️ Could not save user profile: {e}")
        return None


# ─── Study Notes / Summaries / Explanations ─────────────────────────────────

def save_note(user_id: str, title: str, content: str) -> bool:
    """Save a study note (summary or explanation) for a user."""
    try:
        sb = get_supabase()
        sb.table("study_notes").insert(
            {"user_id": user_id, "title": title, "content": content}
        ).execute()
        return True
    except Exception as e:
        st.warning(f"⚠️ Could not save note: {e}")
        return False


def get_notes(user_id: str) -> list[dict]:
    """Retrieve all saved notes for a user, newest first."""
    try:
        sb = get_supabase()
        result = sb.table("study_notes") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .execute()
        return result.data or []
    except Exception as e:
        st.warning(f"⚠️ Could not fetch notes: {e}")
        return []


def delete_note(note_id: str) -> bool:
    """Delete a study note by its UUID."""
    try:
        sb = get_supabase()
        sb.table("study_notes").delete().eq("id", note_id).execute()
        return True
    except Exception as e:
        st.warning(f"⚠️ Could not delete note: {e}")
        return False


# ─── Quiz Results ────────────────────────────────────────────────────────────

def save_quiz_result(user_id: str, topic: str, score: int, total: int) -> bool:
    """Save a quiz score for a user."""
    try:
        sb = get_supabase()
        sb.table("quiz_results").insert(
            {"user_id": user_id, "topic": topic, "score": score, "total": total}
        ).execute()
        return True
    except Exception as e:
        st.warning(f"⚠️ Could not save quiz result: {e}")
        return False


def get_quiz_history(user_id: str, limit: int = 10) -> list[dict]:
    """Retrieve recent quiz results for a user."""
    try:
        sb = get_supabase()
        result = sb.table("quiz_results") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        return result.data or []
    except Exception as e:
        st.warning(f"⚠️ Could not fetch quiz history: {e}")
        return []


# ─── Flashcard Sets ──────────────────────────────────────────────────────────

def save_flashcard_set(user_id: str, topic: str, cards: list[dict]) -> bool:
    """Save a flashcard set for a user."""
    try:
        sb = get_supabase()
        sb.table("flashcard_sets").insert(
            {"user_id": user_id, "topic": topic, "cards": json.dumps(cards)}
        ).execute()
        return True
    except Exception as e:
        st.warning(f"⚠️ Could not save flashcard set: {e}")
        return False


def get_flashcard_sets(user_id: str) -> list[dict]:
    """Retrieve all saved flashcard sets for a user, newest first."""
    try:
        sb = get_supabase()
        result = sb.table("flashcard_sets") \
            .select("id, topic, cards, created_at") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .execute()
        sets = result.data or []
        # Parse cards JSON if returned as string
        for s in sets:
            if isinstance(s.get("cards"), str):
                try:
                    s["cards"] = json.loads(s["cards"])
                except Exception:
                    s["cards"] = []
        return sets
    except Exception as e:
        st.warning(f"⚠️ Could not fetch flashcard sets: {e}")
        return []


# ─── Chat History ────────────────────────────────────────────────────────────

def save_chat_history(user_id: str, messages: list[dict]) -> bool:
    """
    Upsert chat history for a user.
    Stores only role + content (strips audio bytes for DB storage).
    """
    if not user_id or not str(user_id).strip():
        return False
    try:
        sb = get_supabase()
        clean_msgs = [
            {"role": m.get("role", "user"), "content": str(m.get("content", "") or "")}
            for m in messages
        ]
        # Check if row exists
        existing = sb.table("chat_history") \
            .select("id") \
            .eq("user_id", user_id) \
            .execute()
        if existing.data:
            sb.table("chat_history") \
                .update({"messages": json.dumps(clean_msgs)}) \
                .eq("user_id", user_id) \
                .execute()
        else:
            sb.table("chat_history") \
                .insert({"user_id": user_id, "messages": json.dumps(clean_msgs)}) \
                .execute()
        return True
    except Exception as e:
        st.warning(f"⚠️ Could not save chat history: {e}")
        return False


def get_chat_history(user_id: str) -> list[dict]:
    """Retrieve last saved chat history for a user."""
    try:
        sb = get_supabase()
        result = sb.table("chat_history") \
            .select("messages") \
            .eq("user_id", user_id) \
            .execute()
        if result.data and result.data[0].get("messages"):
            msgs = result.data[0]["messages"]
            if isinstance(msgs, str):
                msgs = json.loads(msgs)
            return msgs
        return []
    except Exception as e:
        st.warning(f"⚠️ Could not fetch chat history: {e}")
        return []
