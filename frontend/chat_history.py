from firebase_admin import firestore as admin_firestore
from datetime import datetime
import uuid
import os

_db = None

def _get_db():
    global _db
    if _db is None:
        try:
            _db = admin_firestore.client()
        except Exception as e:
            print(f"Firestore Client Initialization Error: {e}")
            return None
    return _db


def save_chat(user_id: str, chat_id: str, messages: list, title: str = ""):
    """Save or update a specific chat for a user."""
    try:
        db = _get_db()
        if db is None:
            print("Cannot save chat: Firestore not initialized.")
            return

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
        print(f"Chat {chat_id} saved successfully for user {user_id}")
    except Exception as e:
        print(f"Error saving chat: {e}")


def load_chat(user_id: str, chat_id: str) -> list:
    """Load a specific chat's messages."""
    try:
        db = _get_db()
        if db is None:
            return []
        doc_ref = db.collection("users").document(user_id).collection("chats").document(chat_id)
        doc = doc_ref.get(timeout=15)
        if doc.exists:
            return doc.to_dict().get("messages", [])
    except Exception as e:
        print(f"Error loading chat {chat_id}: {e}")
    return []


def get_all_chats(user_id: str) -> list:
    """Get all chat sessions for a user, sorted by most recent."""
    try:
        db = _get_db()
        if db is None:
            return []
        chats_ref = db.collection("users").document(user_id).collection("chats")
        # Ensure Query.DESCENDING is accessed correctly via the module
        from google.cloud.firestore_v1.query import Query
        docs = chats_ref.order_by("updated_at", direction=Query.DESCENDING).get(timeout=15)
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
        print(f"Error getting all chats for user {user_id}: {e}")
        return []


def delete_chat(user_id: str, chat_id: str):
    """Delete a specific chat."""
    try:
        db = _get_db()
        if db is None:
            return
        db.collection("users").document(user_id).collection("chats").document(chat_id).delete()
        print(f"Chat {chat_id} deleted successfully.")
    except Exception as e:
        print(f"Error deleting chat {chat_id}: {e}")


def new_chat_id() -> str:
    """Generate a unique chat ID."""
    return str(uuid.uuid4())[:8]