from google.cloud import firestore
from firebase_admin import firestore as admin_firestore
from datetime import datetime
import uuid
import os

# ============================================================
# LAZY Firestore client — only connect when first used.
# DO NOT call admin_firestore.client() at module level;
# it hangs if Firebase isn't ready yet.
# ============================================================
_db = None

def _get_db():
    global _db
    if _db is None:
        _db = admin_firestore.client()
    return _db


def save_chat(user_id: str, chat_id: str, messages: list, title: str = ""):
    """Save or update a specific chat for a user."""
    try:
        db = _get_db()
        if not title and messages:
            for msg in messages:
                if msg["role"] == "user":
                    title = msg["content"][:40]
                    break
            if not title:
                title = "New Chat"

        doc_ref = db.collection("users").document(user_id).collection("chats").document(chat_id)
        doc_ref.set({
            "messages": messages,
            "title": title,
            "updated_at": datetime.utcnow().isoformat()
        })
    except Exception as e:
        print(f"Error saving chat: {e}")


def load_chat(user_id: str, chat_id: str) -> list:
    """Load a specific chat's messages."""
    try:
        db = _get_db()
        doc_ref = db.collection("users").document(user_id).collection("chats").document(chat_id)
        doc = doc_ref.get(timeout=10)
        if doc.exists:
            return doc.to_dict().get("messages", [])
    except Exception as e:
        print(f"Error loading chat: {e}")
    return []


def get_all_chats(user_id: str) -> list:
    """Get all chat sessions for a user, sorted by most recent."""
    try:
        db = _get_db()
        chats_ref = db.collection("users").document(user_id).collection("chats")
        docs = chats_ref.order_by("updated_at", direction=firestore.Query.DESCENDING).get(timeout=10)
        chats = []
        for doc in docs:
            data = doc.to_dict()
            chats.append({
                "id": doc.id,
                "title": data.get("title", "Untitled"),
                "updated_at": data.get("updated_at", ""),
            })
        return chats
    except Exception as e:
        print(f"Error getting all chats: {e}")
        return []


def delete_chat(user_id: str, chat_id: str):
    """Delete a specific chat."""
    try:
        db = _get_db()
        db.collection("users").document(user_id).collection("chats").document(chat_id).delete()
    except Exception as e:
        print(f"Error deleting chat: {e}")


def new_chat_id() -> str:
    """Generate a unique chat ID."""
    return str(uuid.uuid4())[:8]