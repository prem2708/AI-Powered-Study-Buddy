"""
auth.py — Clerk JWT verification for StudyBuddy
Verifies Clerk session tokens using the JWKS public key endpoint.
"""

import os
import streamlit as st
import requests
import jwt                  # PyJWT
from jwt.algorithms import RSAAlgorithm
from dotenv import load_dotenv

load_dotenv()

_JWKS_CACHE: dict = {}


def _get_jwks() -> dict:
    """Fetch and cache Clerk's JWKS (JSON Web Key Set)."""
    global _JWKS_CACHE
    if _JWKS_CACHE:
        return _JWKS_CACHE

    jwks_url = os.getenv("CLERK_JWKS_URL", "")
    if not jwks_url:
        raise ValueError("CLERK_JWKS_URL is not set in .env")

    resp = requests.get(jwks_url, timeout=10)
    resp.raise_for_status()
    _JWKS_CACHE = resp.json()
    return _JWKS_CACHE


def verify_clerk_jwt(token: str) -> dict:
    """
    Verify a Clerk JWT session token.
    Returns decoded payload dict with keys: sub (user_id), email, name, etc.
    Raises jwt.PyJWTError on invalid/expired token.
    """
    jwks = _get_jwks()
    # Decode header to find key id
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    # Find matching public key
    public_key = None
    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == kid:
            public_key = RSAAlgorithm.from_jwk(key_data)
            break

    if public_key is None:
        raise jwt.InvalidTokenError("No matching public key found in JWKS")

    payload = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        options={"verify_aud": False},  # Clerk doesn't enforce audience by default
    )
    return payload


def get_current_user() -> dict | None:
    """
    Read the verified user from Streamlit session state.
    Returns the user dict if logged in, else None.
    """
    return st.session_state.get("clerk_user", None)


def clear_session():
    """Clear the current user session."""
    for key in ["clerk_user", "clerk_token"]:
        st.session_state.pop(key, None)
