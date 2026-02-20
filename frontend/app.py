import streamlit as st
import os
import time
import requests
import base64
import json
import threading
from auth import sign_up, login, is_firebase_initialized
from chat_history import save_chat, load_chat, get_all_chats, delete_chat, new_chat_id

BACKEND_URL = os.getenv("BACKEND_URL", "https://talent-scouting.vercel.app/")

# ============================================================
# Page Configuration
# ============================================================
st.set_page_config(
    page_title="TalentScout AI Hiring Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ... (CSS remains same)

# ============================================================
# Session State Initialization
# ============================================================
defaults = {
    "authenticated": False,
    "user_email": "",
    "user_id": "",
    "is_guest": False,
    "messages": [],
    "current_chat_id": "",
    "conversation_state": None,
    "candidate_info": None,
    "tech_questions": None,
    "conversation_ended": False,
    "greeting_shown": False,
    "temperature": 0.7,
    "parsed_document_context": None,
    "clear_uploader": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# Firestore helpers — all wrapped with hard timeouts
# so they NEVER block the UI thread
# ============================================================
def _run_with_timeout(fn, timeout=15):
    """Run fn() in a thread. Return (result, error). Never hangs."""
    if not is_firebase_initialized():
        return None, Exception("Firebase not initialized")

    result_holder = [None]
    error_holder = [None]
    def worker():
        try:
            result_holder[0] = fn()
        except Exception as e:
            error_holder[0] = e
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        return None, TimeoutError(f"Firestore call timed out after {timeout}s")
    return result_holder[0], error_holder[0]

def safe_get_all_chats(user_id):
    result, err = _run_with_timeout(lambda: get_all_chats(user_id), timeout=15)
    if err:
        print(f"safe_get_all_chats error: {err}")
        return []
    return result or []

def safe_load_chat(user_id, chat_id):
    result, err = _run_with_timeout(lambda: load_chat(user_id, chat_id), timeout=15)
    if err:
        print(f"safe_load_chat error: {err}")
        return None # Return None to indicate error rather than empty list
    return result

def safe_save_chat(user_id, chat_id, messages):
    if not is_firebase_initialized():
        return
    # Fire and forget in background — never block UI
    t = threading.Thread(
        target=lambda: save_chat(user_id, chat_id, messages),
        daemon=True
    )
    t.start()

def format_resume_output(parsed_data):
    output = "**Resume Analysis Complete**\n\n"
    if parsed_data.get("personal_detail"):
        output += "**Personal Information:**\n"
        pd = parsed_data["personal_detail"]
        for key, label in [("full_name","Name"),("email","Email"),("contact_no","Phone"),("gender","Gender"),("nationality","Nationality")]:
            if pd.get(key): output += f"- {label}: {pd[key]}\n"
        output += "\n"
    if parsed_data.get("address"):
        addr = parsed_data["address"]
        parts = [addr.get(k,"") for k in ["address","city","state","country","zip_code"] if addr.get(k)]
        output += f"**Address:**\n{', '.join(parts)}\n\n"
    if parsed_data.get("education"):
        output += "**Education:**\n"
        for edu in parsed_data["education"]:
            output += f"- {edu.get('degree','N/A')}"
            if edu.get("school"): output += f" from {edu['school']}"
            if edu.get("start_date") or edu.get("end_date"):
                output += f" ({edu.get('start_date','')} - {edu.get('end_date','')})"
            output += "\n"
        output += "\n"
    if parsed_data.get("experience"):
        output += "**Work Experience:**\n"
        for exp in parsed_data["experience"]:
            output += f"- {exp.get('job_title','N/A')}"
            if exp.get("company_name"): output += f" at {exp['company_name']}"
            if exp.get("start_date") or exp.get("end_date"):
                output += f" ({exp.get('start_date','')} - {exp.get('end_date','')})"
            output += "\n"
            if exp.get("projects"): output += f"  {exp['projects']}\n"
        output += "\n"
    if parsed_data.get("skills"):
        skills = parsed_data["skills"]
        output += "**Skills:**\n" + (", ".join(skills) if isinstance(skills, list) else str(skills)) + "\n\n"
    if parsed_data.get("certifications"):
        output += "**Certifications:**\n"
        certs = parsed_data["certifications"]
        if isinstance(certs, list):
            for c in certs: output += f"- {c}\n"
        else:
            output += f"- {certs}\n"
        output += "\n"
    return output

def format_jd_output(parsed_data):
    output = "**Job Description Analysis Complete**\n\n"
    if parsed_data.get("job_detail"):
        jd = parsed_data["job_detail"]
        output += "**Position Details:**\n"
        for key, label in [("job_position","Position"),("job_type","Type"),("job_shift","Shift"),("job_industry","Industry"),("closing_date","Application Deadline"),("no_of_openings","Number of Openings")]:
            if jd.get(key): output += f"- {label}: {jd[key]}\n"
        if jd.get("min_experience") or jd.get("max_experience"):
            output += f"- Experience Required: {jd.get('min_experience',0)}-{jd.get('max_experience',0)} years\n"
        output += "\n"
        if jd.get("required_education"):
            output += "**Education Requirements:**\n"
            edu = jd["required_education"]
            if isinstance(edu, list):
                for e in edu: output += f"- {e}\n"
            else:
                output += f"- {edu}\n"
            output += "\n"
        if jd.get("job_description"):
            output += f"**Description:**\n{jd['job_description']}\n\n"
    if parsed_data.get("salary_range"):
        sal = parsed_data["salary_range"]
        if sal.get("min_amount") or sal.get("max_amount"):
            output += f"**Salary Range:**\n${sal.get('min_amount',0):,} - ${sal.get('max_amount',0):,}\n\n"
    if parsed_data.get("job_location"):
        loc = parsed_data["job_location"]
        parts = [loc.get(k,"") for k in ["city","state","country","zip_code"] if loc.get(k)]
        output += f"**Location:**\n{', '.join(parts)}\n\n"
    if parsed_data.get("required_skills"):
        skills = parsed_data["required_skills"]
        output += "**Required Skills:**\n" + (", ".join(skills) if isinstance(skills, list) else str(skills)) + "\n"
    return output

# ============================================================
# ROUTING — top-level if/else
# ============================================================

if not st.session_state.authenticated:
    # --------------------------------------------------------
    # LOGIN PAGE
    # KEY FIX: On successful login we ONLY set session state
    # and call st.rerun(). Zero Firestore calls here.
    # Firestore is loaded lazily in the chat page sidebar.
    # --------------------------------------------------------
    st.markdown("<h1 style='text-align:center;'>TalentScout AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#888;'>Sign in to access the hiring assistant</p>", unsafe_allow_html=True)
    st.markdown("")

    tab_login, tab_signup = st.tabs(["  Login  ", "  Sign Up  "])

    with tab_login:
        st.markdown("")
        email = st.text_input("Email", placeholder="you@example.com", key="login_email")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
        st.markdown("")

        if st.button("Log In", key="login_btn", use_container_width=True):
            if not email or not password:
                st.error("Please fill in both fields.")
            else:
                with st.spinner("Logging in..."):
                    result = login(email, password)

                if result["success"]:
                    # ✅ ONLY set session state — NO Firestore here
                    st.session_state.authenticated = True
                    st.session_state.user_email = result["user"]["email"]
                    st.session_state.user_id = result["user"]["localId"]
                    st.session_state.is_guest = False
                    st.session_state.current_chat_id = new_chat_id()
                    st.session_state.messages = []
                    st.rerun()  # immediately goes to chat page
                else:
                    st.error(result["message"])

    with tab_signup:
        st.markdown("")
        new_email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
        new_password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="••••••••", key="signup_confirm")
        st.markdown("")

        if st.button("Create Account", key="signup_btn", use_container_width=True):
            if not new_email or not new_password:
                st.error("Please fill in all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                with st.spinner("Creating account..."):
                    result = sign_up(new_email, new_password)
                if result["success"]:
                    # ✅ ONLY set session state — NO Firestore here
                    st.session_state.authenticated = True
                    st.session_state.user_email = result["user"]["email"]
                    st.session_state.user_id = result["user"]["localId"]
                    st.session_state.is_guest = False
                    st.session_state.current_chat_id = new_chat_id()
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.error(result["message"])

    st.markdown("---")
    st.markdown("<p style='text-align:center;color:#888;font-size:0.9rem;'>or</p>", unsafe_allow_html=True)
    if st.button("👤 Continue as Guest", use_container_width=True, key="guest_btn"):
        st.session_state.authenticated = True
        st.session_state.user_email = "Guest"
        st.session_state.is_guest = True
        st.session_state.current_chat_id = new_chat_id()
        st.rerun()

else:
    # --------------------------------------------------------
    # CHAT PAGE
    # Firestore history loads here lazily — never blocks login
    # --------------------------------------------------------

    with st.sidebar:
        if st.session_state.is_guest:
            st.markdown("**👤 Guest Mode**")
            st.caption("Sign in to save your chats")
        else:
            st.markdown("**Logged in as:**")
            st.markdown(f"`{st.session_state.user_email}`")
        st.markdown("---")

        def start_new_chat():
            if not st.session_state.is_guest and st.session_state.messages:
                safe_save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)
            st.session_state.current_chat_id = new_chat_id()
            st.session_state.messages = []
            st.session_state.conversation_state = None
            st.session_state.candidate_info = None
            st.session_state.tech_questions = None
            st.session_state.conversation_ended = False
            st.session_state.greeting_shown = False
            st.session_state.parsed_document_context = None
            st.session_state.clear_uploader = False

        st.button("➕ New Chat", use_container_width=True, on_click=start_new_chat)

        if not st.session_state.is_guest:
            st.markdown("### 💬 Chat History")
            # Load history with timeout — never hangs
            all_chats = safe_get_all_chats(st.session_state.user_id)
            if all_chats:
                for chat in all_chats:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        is_active = chat["id"] == st.session_state.current_chat_id
                        label = f"{'▶ ' if is_active else ''}{chat['title']}"
                        if st.button(label, key=f"chat_{chat['id']}", use_container_width=True):
                            if st.session_state.messages:
                                safe_save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)
                            
                            loaded_messages = safe_load_chat(st.session_state.user_id, chat["id"])
                            if loaded_messages is not None:
                                st.session_state.current_chat_id = chat["id"]
                                st.session_state.messages = loaded_messages
                                st.rerun()
                            else:
                                st.error("Failed to load chat. Please try again.")
                    with col2:
                        if st.button("🗑", key=f"del_{chat['id']}"):
                            _run_with_timeout(lambda: delete_chat(st.session_state.user_id, chat["id"]))
                            if chat["id"] == st.session_state.current_chat_id:
                                st.session_state.current_chat_id = new_chat_id()
                                st.session_state.messages = []
                            st.rerun()
            else:
                st.caption("No previous chats")

        st.markdown("---")
        st.header("Chat Settings")
        st.markdown("**Model:**")
        st.info("Groq Llama 3.3 70B (Active)")
        st.caption("Coming Soon: GPT-4, Claude, Gemini")
        st.markdown("**Temperature:**")
        st.session_state.temperature = st.slider(
            "Adjust response creativity",
            min_value=0.0, max_value=1.0,
            value=st.session_state.temperature, step=0.1,
        )
        st.caption(f"Current: {st.session_state.temperature}")
        st.markdown("---")

        logout_label = "🚪 Exit Guest Mode" if st.session_state.is_guest else "🚪 Logout"
        if st.button(logout_label, use_container_width=True):
            if not st.session_state.is_guest and st.session_state.messages:
                safe_save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)
            for k, v in defaults.items():
                st.session_state[k] = v
            st.rerun()

    # Main chat area
    st.title("TalentScout Hiring Assistant")
    st.markdown("Welcome to TalentScout. This assistant will conduct your initial screening interview.")

    if not st.session_state.greeting_shown and len(st.session_state.messages) == 0:
        greeting = """Hello and welcome to TalentScout. I am your AI Hiring Assistant.

My objective is to conduct an initial screening interview with you. During this process, I will:
- Collect essential information about your background and experience
- Understand your technical skills and expertise
- Ask relevant technical questions based on your tech stack

This conversation will take approximately 5-10 minutes. Let's begin - could you please tell me your full name?"""
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.greeting_shown = True
        if not st.session_state.is_guest:
            safe_save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.clear_uploader:
        st.session_state.clear_uploader = False
        st.rerun()

    upload_col1, upload_col2, upload_col3, _ = st.columns([1.5, 2.5, 2, 6])
    with upload_col1:
        parse_type = st.selectbox("Type", ["Resume","JD"], key="parse_type_select", label_visibility="collapsed")
    with upload_col2:
        uploaded_file = st.file_uploader("Upload", type=["pdf","docx","txt"], key="file_uploader", label_visibility="collapsed")
    with upload_col3:
        if uploaded_file and st.button("📄 Parse", use_container_width=True):
            file_bytes = uploaded_file.read()
            file_b64 = base64.b64encode(file_bytes).decode("utf-8")
            endpoint = "/parse/resume" if parse_type == "Resume" else "/parse/jd"
            payload = {"fileName": uploaded_file.name, "fileContent": file_b64}
            st.session_state.messages.append({"role": "user", "content": f"Uploaded {uploaded_file.name} for {parse_type} parsing"})
            with st.spinner(f"Parsing {parse_type.lower()}..."):
                try:
                    resp = requests.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=60)
                    if resp.status_code == 200:
                        parsed = resp.json()
                        st.session_state.parsed_document_context = {"type": parse_type, "filename": uploaded_file.name, "data": parsed}
                        formatted = format_resume_output(parsed) if parse_type == "Resume" else format_jd_output(parsed)
                        formatted += f"\n\n**Document loaded into context.** You can now ask me questions about this {parse_type.lower()}."
                        st.session_state.messages.append({"role": "assistant", "content": formatted})
                    else:
                        st.session_state.messages.append({"role": "assistant", "content": f"Error: {resp.json().get('detail','Unknown error')}"})
                except Exception as e:
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})
            if not st.session_state.is_guest:
                safe_save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)
            st.session_state.clear_uploader = True
            st.rerun()

    if prompt := st.chat_input("Type your message here..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            with st.spinner("Thinking..."):
                try:
                    message_with_context = prompt
                    if st.session_state.parsed_document_context:
                        doc_ctx = st.session_state.parsed_document_context
                        message_with_context = (
                            f"[DOCUMENT CONTEXT - {doc_ctx['type']}: {doc_ctx['filename']}]\n"
                            f"Document Data: {json.dumps(doc_ctx['data'])}\n\n"
                            f"User Question: {prompt}"
                        )
                    resp = requests.post(
                        f"{BACKEND_URL}/chat/hiring",
                        json={"message": message_with_context, "conversation_state": st.session_state.conversation_state},
                        timeout=60
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        assistant_response = data["response"]
                        st.session_state.conversation_state = data["conversation_state"]
                        if data.get("candidate_info"): st.session_state.candidate_info = data["candidate_info"]
                        if data.get("tech_questions"): st.session_state.tech_questions = data["tech_questions"]
                        for chunk in assistant_response.split():
                            full_response += chunk + " "
                            time.sleep(0.02)
                            message_placeholder.markdown(full_response + "▌")
                        message_placeholder.markdown(full_response)
                        if data.get("conversation_ended"):
                            st.session_state.conversation_ended = True
                    else:
                        full_response = f"❌ Error: {resp.json().get('detail','Unknown error')}"
                        message_placeholder.markdown(full_response)
                except requests.exceptions.ConnectionError:
                    full_response = "❌ Cannot connect to backend."
                    message_placeholder.markdown(full_response)
                except Exception as e:
                    full_response = f"❌ Error: {str(e)}"
                    message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        if not st.session_state.is_guest:
            safe_save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)

    if st.session_state.get("candidate_info"):
        with st.sidebar:
            st.markdown("---")
            st.markdown("### Candidate Profile")
            info = st.session_state.candidate_info
            for key, label in [("full_name","Name"),("email","Email"),("phone","Phone"),("years_of_experience","Experience"),("desired_position","Position"),("current_location","Location")]:
                if info.get(key): st.markdown(f"**{label}:** {info[key]}")
            if info.get("tech_stack"):
                tech_list = info["tech_stack"] if isinstance(info["tech_stack"], list) else [info["tech_stack"]]
                st.markdown(f"**Tech Stack:** {', '.join(tech_list)}")