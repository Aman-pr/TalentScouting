import requests
import json
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth

# Build path relative to this file
_DIR = os.path.dirname(os.path.abspath(__file__))
_CRED_PATH = os.path.join(_DIR, "talentscout-jb-475c123a5377.json")

# ============================================================
# IMPORTANT: Replace this with your Firebase Web API Key
# Found in: Firebase Console -> Project Settings -> General -> Web API Key
# ============================================================
FIREBASE_API_KEY = "AIzaSyBGTkTYUlzxjgb6QooU-IAmimWIWS0VElM"

# Firebase Initialization
FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT")
firebase_initialized = False

# 1. Try environment variable (Best for Cloud/Production)
if FIREBASE_SERVICE_ACCOUNT:
    try:
        cred_dict = json.loads(FIREBASE_SERVICE_ACCOUNT)
        crd = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(crd)
        firebase_initialized = True
        print("Firebase initialized using FIREBASE_SERVICE_ACCOUNT env variable.")
    except Exception as e:
        print(f"Failed to initialize Firebase from environment variable: {e}")

# 2. Try local JSON file (Fallback for local dev)
if not firebase_initialized:
    if os.path.exists(_CRED_PATH):
        try:
            crd = credentials.Certificate(_CRED_PATH)
            firebase_admin.initialize_app(crd)
            firebase_initialized = True
            print(f"Firebase initialized using service account file: {_CRED_PATH}")
        except Exception as e:
            print(f"Failed to initialize Firebase from file: {e}")
    else:
        print(f"Firebase credentials not found (checked env and {_CRED_PATH})")

# 3. Final Check
if not firebase_initialized:
    print("WARNING: Firebase not initialized. Authentication features will fail.")

def is_firebase_initialized() -> bool:
    """Check if Firebase has been successfully initialized."""
    return firebase_initialized


FIREBASE_SIGNUP_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
FIREBASE_LOGIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"


def sign_up(email: str, password: str) -> dict:
    """
    Create a new user with email and password using Firebase REST API.
    Returns a dict with 'success' (bool), 'message' (str), and optionally 'user' data.
    """
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    try:
        response = requests.post(FIREBASE_SIGNUP_URL, json=payload, timeout=10)
        data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "message": "Account created successfully!",
                "user": {
                    "email": data.get("email"),
                    "localId": data.get("localId"),
                    "idToken": data.get("idToken"),
                }
            }
        else:
            error_message = data.get("error", {}).get("message", "Unknown error")
            return {"success": False, "message": _friendly_error(error_message)}

    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Network error: {str(e)}"}


def login(email: str, password: str) -> dict:
    """
    Sign in an existing user with email and password using Firebase REST API.
    Returns a dict with 'success' (bool), 'message' (str), and optionally 'user' data.
    """
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    try:
        response = requests.post(FIREBASE_LOGIN_URL, json=payload, timeout=10)
        data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "message": "Login successful!",
                "user": {
                    "email": data.get("email"),
                    "localId": data.get("localId"),
                    "idToken": data.get("idToken"),
                    "displayName": data.get("displayName", ""),
                }
            }
        else:
            error_message = data.get("error", {}).get("message", "Unknown error")
            return {"success": False, "message": _friendly_error(error_message)}

    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Network error: {str(e)}"}


def _friendly_error(firebase_error: str) -> str:
    """Convert Firebase error codes to user-friendly messages."""
    error_map = {
        "EMAIL_EXISTS": "This email is already registered. Please log in.",
        "INVALID_EMAIL": "Please enter a valid email address.",
        "WEAK_PASSWORD": "Password must be at least 6 characters.",
        "EMAIL_NOT_FOUND": "No account found with this email.",
        "INVALID_PASSWORD": "Incorrect password. Please try again.",
        "INVALID_LOGIN_CREDENTIALS": "Invalid email or password.",
        "USER_DISABLED": "This account has been disabled.",
        "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many attempts. Please try again later.",
    }
    return error_map.get(firebase_error, f"Error: {firebase_error}")
