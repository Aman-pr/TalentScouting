from google.cloud import firestore
from firebase_admin import firestore as admin_firestore
from datetime import datetime
import uuid
import os

# Note: Firestore client is initialized using the default app set up in auth.py
db = admin_firestore.client()


def save_chat(user_id: str, chat_id: str, messages: list, title: str = ""):
    """Save or update a specific chat for a user."""
    if not title and messages:
        # Use first user message as title (truncated)
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


def load_chat(user_id: str, chat_id: str) -> list:
    """Load a specific chat's messages."""
    doc_ref = db.collection("users").document(user_id).collection("chats").document(chat_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get("messages", [])
    return []


def get_all_chats(user_id: str) -> list:
    """Get all chat sessions for a user, sorted by most recent."""
    chats_ref = db.collection("users").document(user_id).collection("chats")
    docs = chats_ref.order_by("updated_at", direction=firestore.Query.DESCENDING).stream()
    chats = []
    for doc in docs:
        data = doc.to_dict()
        chats.append({
            "id": doc.id,
            "title": data.get("title", "Untitled"),
            "updated_at": data.get("updated_at", ""),
        })
    return chats


def delete_chat(user_id: str, chat_id: str):
    """Delete a specific chat."""
    db.collection("users").document(user_id).collection("chats").document(chat_id).delete()


def new_chat_id() -> str:
    """Generate a unique chat ID."""
    return str(uuid.uuid4())[:8]
