
import streamlit as st
import os
import time
import requests
import base64
import json
from auth import sign_up, login
from chat_history import save_chat, load_chat, get_all_chats, delete_chat, new_chat_id

# If running in Docker/Cloud with Nginx, the API is served at /api
BACKEND_URL = os.getenv("BACKEND_URL", "https://talent-scouting.vercel.app/docs#/default/parse_resume_parse_resume_post")
if not BACKEND_URL.endswith("/api") and os.getenv("ENVIRONMENT") == "production":
    BACKEND_URL = BACKEND_URL.rstrip("/") + "/api"

def format_resume_output(parsed_data):
    """Format resume JSON data as readable text."""
    output = "**Resume Analysis Complete**\n\n"
    
    # Personal Details
    if parsed_data.get("personal_detail"):
        output += "**Personal Information:**\n"
        pd = parsed_data["personal_detail"]
        if pd.get("full_name"):
            output += f"- Name: {pd['full_name']}\n"
        if pd.get("email"):
            output += f"- Email: {pd['email']}\n"
        if pd.get("contact_no"):
            output += f"- Phone: {pd['contact_no']}\n"
        if pd.get("gender"):
            output += f"- Gender: {pd['gender']}\n"
        if pd.get("nationality"):
            output += f"- Nationality: {pd['nationality']}\n"
        output += "\n"
    
    # Address
    if parsed_data.get("address"):
        output += "**Address:**\n"
        addr = parsed_data["address"]
        address_parts = []
        if addr.get("address"):
            address_parts.append(addr["address"])
        if addr.get("city"):
            address_parts.append(addr["city"])
        if addr.get("state"):
            address_parts.append(addr["state"])
        if addr.get("country"):
            address_parts.append(addr["country"])
        if addr.get("zip_code"):
            address_parts.append(addr["zip_code"])
        output += f"{', '.join(address_parts)}\n\n"
    
    # Education
    if parsed_data.get("education"):
        output += "**Education:**\n"
        for edu in parsed_data["education"]:
            output += f"- {edu.get('degree', 'N/A')}"
            if edu.get("school"):
                output += f" from {edu['school']}"
            if edu.get("start_date") or edu.get("end_date"):
                output += f" ({edu.get('start_date', '')} - {edu.get('end_date', '')})"
            output += "\n"
        output += "\n"
    
    # Experience
    if parsed_data.get("experience"):
        output += "**Work Experience:**\n"
        for exp in parsed_data["experience"]:
            output += f"- {exp.get('job_title', 'N/A')}"
            if exp.get("company_name"):
                output += f" at {exp['company_name']}"
            if exp.get("start_date") or exp.get("end_date"):
                output += f" ({exp.get('start_date', '')} - {exp.get('end_date', '')})"
            output += "\n"
            if exp.get("projects"):
                output += f"  {exp['projects']}\n"
        output += "\n"
    
    # Skills
    if parsed_data.get("skills"):
        output += "**Skills:**\n"
        skills = parsed_data["skills"]
        if isinstance(skills, list):
            output += ", ".join(skills) + "\n\n"
        else:
            output += f"{skills}\n\n"
    
    # Certifications
    if parsed_data.get("certifications"):
        output += "**Certifications:**\n"
        certs = parsed_data["certifications"]
        if isinstance(certs, list):
            for cert in certs:
                output += f"- {cert}\n"
        else:
            output += f"- {certs}\n"
        output += "\n"
    
    return output

def format_jd_output(parsed_data):
    """Format job description JSON data as readable text."""
    output = "**Job Description Analysis Complete**\n\n"
    
    if parsed_data.get("job_detail"):
        jd = parsed_data["job_detail"]
        output += "**Position Details:**\n"
        if jd.get("job_position"):
            output += f"- Position: {jd['job_position']}\n"
        if jd.get("job_type"):
            output += f"- Type: {jd['job_type']}\n"
        if jd.get("job_shift"):
            output += f"- Shift: {jd['job_shift']}\n"
        if jd.get("job_industry"):
            output += f"- Industry: {jd['job_industry']}\n"
        if jd.get("closing_date"):
            output += f"- Application Deadline: {jd['closing_date']}\n"
        if jd.get("min_experience") or jd.get("max_experience"):
            output += f"- Experience Required: {jd.get('min_experience', 0)}-{jd.get('max_experience', 0)} years\n"
        if jd.get("no_of_openings"):
            output += f"- Number of Openings: {jd['no_of_openings']}\n"
        output += "\n"
        
        if jd.get("required_education"):
            output += "**Education Requirements:**\n"
            edu = jd["required_education"]
            if isinstance(edu, list):
                for e in edu:
                    output += f"- {e}\n"
            else:
                output += f"- {edu}\n"
            output += "\n"
        
        if jd.get("job_description"):
            output += f"**Description:**\n{jd['job_description']}\n\n"
    
    if parsed_data.get("salary_range"):
        sal = parsed_data["salary_range"]
        output += "**Salary Range:**\n"
        if sal.get("min_amount") or sal.get("max_amount"):
            output += f"${sal.get('min_amount', 0):,} - ${sal.get('max_amount', 0):,}\n\n"
    
    if parsed_data.get("job_location"):
        loc = parsed_data["job_location"]
        output += "**Location:**\n"
        location_parts = []
        if loc.get("city"): location_parts.append(loc["city"])
        if loc.get("state"): location_parts.append(loc["state"])
        if loc.get("country"): location_parts.append(loc["country"])
        if loc.get("zip_code"): location_parts.append(loc["zip_code"])
        output += f"{', '.join(location_parts)}\n\n"
    
    if parsed_data.get("required_skills"):
        output += "**Required Skills:**\n"
        skills = parsed_data["required_skills"]
        output += (", ".join(skills) if isinstance(skills, list) else str(skills)) + "\n"
    
    return output

# Page Configuration
st.set_page_config(
    page_title="TalentScout AI Hiring Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern dark theme
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #1a1a1a; border-right: 1px solid #333333; }
    h1, h2, h3, p, div, span, label { color: #ffffff !important; }
    .stChatInputContainer { padding-bottom: 20px; }
    header { background-color: transparent !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .login-container {
        max-width: 420px;
        margin: 60px auto;
        padding: 40px 36px;
        background: #111111;
        border-radius: 16px;
        border: 1px solid #2a2a2a;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    .login-header { text-align: center; margin-bottom: 8px; font-size: 2rem; font-weight: 700; }
    .login-sub { text-align: center; color: #888888 !important; font-size: 0.95rem; margin-bottom: 28px; }

    .stTabs [data-baseweb="tab-list"] { gap: 0px; justify-content: center; background-color: #1a1a1a; border-radius: 10px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; color: #888888; padding: 8px 24px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #333333 !important; color: #ffffff !important; }

    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #818cf8, #a78bfa);
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }

    .stTextInput > div > div > input {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Session State Initialization
# ============================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "is_guest" not in st.session_state:
    st.session_state.is_guest = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = ""
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = None
if "candidate_info" not in st.session_state:
    st.session_state.candidate_info = None
if "tech_questions" not in st.session_state:
    st.session_state.tech_questions = None
if "conversation_ended" not in st.session_state:
    st.session_state.conversation_ended = False
if "greeting_shown" not in st.session_state:
    st.session_state.greeting_shown = False
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "parsed_document_context" not in st.session_state:
    st.session_state.parsed_document_context = None
if "clear_uploader" not in st.session_state:
    st.session_state.clear_uploader = False


# ============================================================
# LOGIN / SIGNUP PAGE
# ============================================================
def show_login_page():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<p class="login-header">TalentScout AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Sign in to access the hiring assistant</p>', unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@example.com", key="login_email")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
            submitted = st.form_submit_button("Log In")

            if submitted:
                if not email or not password:
                    st.error("Please fill in both fields.")
                else:
                    with st.spinner("Logging in..."):
                        result = login(email, password)
                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.user_email = result["user"]["email"]
                        st.session_state.user_id = result["user"]["localId"]
                        # Load most recent chat or start new
                        all_chats = get_all_chats(result["user"]["localId"])
                        if all_chats:
                            st.session_state.current_chat_id = all_chats[0]["id"]
                            st.session_state.messages = load_chat(result["user"]["localId"], all_chats[0]["id"])
                        else:
                            st.session_state.current_chat_id = new_chat_id()
                            st.session_state.messages = []
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])

    with tab_signup:
        with st.form("signup_form", clear_on_submit=False):
            new_email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
            new_password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="••••••••", key="signup_confirm")
            submitted = st.form_submit_button("Create Account")

            if submitted:
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
                        st.session_state.authenticated = True
                        st.session_state.user_email = result["user"]["email"]
                        st.session_state.user_id = result["user"]["localId"]
                        st.session_state.current_chat_id = new_chat_id()
                        st.session_state.messages = []
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])

    # Guest mode
    st.markdown("---")
    st.markdown('<p style="text-align:center; color:#888 !important; font-size:0.9rem;">or</p>', unsafe_allow_html=True)
    if st.button("👤 Continue as Guest", use_container_width=True, key="guest_btn"):
        st.session_state.authenticated = True
        st.session_state.user_email = "Guest"
        st.session_state.is_guest = True
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# CHAT PAGE
# ============================================================
def show_chat_page():
    # Sidebar
    with st.sidebar:
        if st.session_state.is_guest:
            st.markdown("**👤 Guest Mode**")
            st.caption("Sign in to save your chats")
        else:
            st.markdown(f"**Logged in as:**")
            st.markdown(f"`{st.session_state.user_email}`")
        st.markdown("---")

        # New Chat button
        def start_new_chat():
            # Save current chat first if it has messages
            if not st.session_state.is_guest and st.session_state.messages:
                save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)
            st.session_state.current_chat_id = new_chat_id()
            st.session_state.messages = []
            # Reset conversation state for new chat
            st.session_state.conversation_state = None
            st.session_state.candidate_info = None
            st.session_state.tech_questions = None
            st.session_state.conversation_ended = False
            st.session_state.greeting_shown = False
            st.session_state.parsed_document_context = None
            st.session_state.clear_uploader = False
            
            # Save empty chat for logged-in users
            if not st.session_state.is_guest:
                save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)

        st.button("➕ New Chat", use_container_width=True, on_click=start_new_chat)

        # Chat History List (only for logged-in users)
        if not st.session_state.is_guest:
            st.markdown("### 💬 Chat History")
            all_chats = get_all_chats(st.session_state.user_id)
            if all_chats:
                for chat in all_chats:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        is_active = chat["id"] == st.session_state.current_chat_id
                        label = f"{'▶ ' if is_active else ''}{chat['title']}"
                        if st.button(label, key=f"chat_{chat['id']}", use_container_width=True):
                            # Save current chat before switching
                            if st.session_state.messages:
                                save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)
                            st.session_state.current_chat_id = chat["id"]
                            st.session_state.messages = load_chat(st.session_state.user_id, chat["id"])
                            st.rerun()
                    with col2:
                        if st.button("🗑", key=f"del_{chat['id']}"):
                            delete_chat(st.session_state.user_id, chat["id"])
                            if chat["id"] == st.session_state.current_chat_id:
                                st.session_state.current_chat_id = new_chat_id()
                                st.session_state.messages = []
                            st.rerun()
            else:
                st.caption("No previous chats")

        st.markdown("---")
        st.header("Chat Settings")
        
        # Model selection - only Groq Llama 3.3 70B is available
        st.markdown("**Model:**")
        st.info("Groq Llama 3.3 70B (Active)")
        st.caption("Coming Soon: GPT-4, Claude, Gemini")
        
        # Temperature slider - functional
        st.markdown("**Temperature:**")
        st.session_state.temperature = st.slider(
            "Adjust response creativity",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.temperature,
            step=0.1,
            help="Lower values make responses more focused and deterministic. Higher values make them more creative."
        )
        st.caption(f"Current: {st.session_state.temperature}")
        st.markdown("---")

        logout_label = "🚪 Exit Guest Mode" if st.session_state.is_guest else "🚪 Logout"
        if st.button(logout_label, use_container_width=True):
            # Save current chat before logout
            if not st.session_state.is_guest and st.session_state.messages:
                save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)
            st.session_state.authenticated = False
            st.session_state.user_email = ""
            st.session_state.user_id = ""
            st.session_state.is_guest = False
            st.session_state.messages = []
            st.session_state.current_chat_id = ""
            st.rerun()

    # Main Chat Interface
    st.title("TalentScout Hiring Assistant")
    st.markdown("Welcome to TalentScout. This assistant will conduct your initial screening interview.")

    # Auto-greeting when new chat is created or website is opened
    if not st.session_state.greeting_shown and len(st.session_state.messages) == 0:
        greeting_message = """Hello and welcome to TalentScout. I am your AI Hiring Assistant.

My objective is to conduct an initial screening interview with you. During this process, I will:
- Collect essential information about your background and experience
- Understand your technical skills and expertise
- Ask relevant technical questions based on your tech stack

This conversation will take approximately 5-10 minutes. Let's begin - could you please tell me your full name?"""
        
        st.session_state.messages.append({"role": "assistant", "content": greeting_message})
        st.session_state.greeting_shown = True
        
        # Save for logged-in users
        if not st.session_state.is_guest:
            save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ---- Document Upload Section (Bottom Left - Compact) ----
    # Clear uploader if flag is set
    if st.session_state.clear_uploader:
        st.session_state.clear_uploader = False
        st.rerun()
    
    upload_col1, upload_col2, upload_col3, upload_col4 = st.columns([1.5, 2.5, 2, 6])
    
    with upload_col1:
        parse_type = st.selectbox(
            "Type",
            ["Resume", "JD"],
            key="parse_type_select",
            label_visibility="collapsed"
        )
    
    with upload_col2:
        uploaded_file = st.file_uploader(
            "Upload",
            type=["pdf", "docx", "txt"],
            key="file_uploader",
            label_visibility="collapsed"
        )
    
    with upload_col3:
        if uploaded_file and st.button("📄 Parse", use_container_width=True):
            file_bytes = uploaded_file.read()
            file_b64 = base64.b64encode(file_bytes).decode("utf-8")
            endpoint = "/parse/resume" if parse_type == "Resume" else "/parse/jd"
            payload = {"fileName": uploaded_file.name, "fileContent": file_b64}

            # Show user message
            user_msg = f"Uploaded {uploaded_file.name} for {parse_type} parsing"
            st.session_state.messages.append({"role": "user", "content": user_msg})

            with st.spinner(f"Parsing {parse_type.lower()}..."):
                try:
                    resp = requests.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=60)
                    if resp.status_code == 200:
                        parsed = resp.json()
                        
                        # Store parsed document in context for RAG
                        st.session_state.parsed_document_context = {
                            "type": parse_type,
                            "filename": uploaded_file.name,
                            "data": parsed
                        }
                        
                        # Format as readable text instead of JSON
                        if parse_type == "Resume":
                            formatted = format_resume_output(parsed)
                        else:
                            formatted = format_jd_output(parsed)
                        
                        # Add context message
                        context_msg = f"\n\n**Document loaded into context.** You can now ask me questions about this {parse_type.lower()}, and I'll answer based on the information provided."
                        formatted += context_msg
                        
                        st.session_state.messages.append({"role": "assistant", "content": formatted})
                    else:
                        error_detail = resp.json().get("detail", "Unknown error")
                        st.session_state.messages.append({"role": "assistant", "content": f"Error: {error_detail}"})
                except requests.exceptions.ConnectionError:
                    st.session_state.messages.append({"role": "assistant", "content": "Cannot connect to backend. Make sure the backend server is running on port 8000.\n\n```bash\ncd backend && python main.py\n```"})
                except Exception as e:
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})

            # Auto-save for logged-in users
            if not st.session_state.is_guest:
                save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)
            
            # Set flag to clear uploader on next rerun
            st.session_state.clear_uploader = True
            st.rerun()



    # React to user input
    if prompt := st.chat_input("Type your message here..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            with st.spinner('Thinking...'):
                try:
                    # Get conversation state from session
                    conversation_state = st.session_state.get("conversation_state", None)
                    
                    # Prepare message with document context if available
                    message_with_context = prompt
                    if st.session_state.parsed_document_context:
                        doc_ctx = st.session_state.parsed_document_context
                        context_info = f"[DOCUMENT CONTEXT - {doc_ctx['type']}: {doc_ctx['filename']}]\n"
                        context_info += f"Document Data: {json.dumps(doc_ctx['data'])}\n\n"
                        context_info += f"User Question: {prompt}"
                        message_with_context = context_info
                    
                    # Call hiring assistant API
                    payload = {
                        "message": message_with_context,
                        "conversation_state": conversation_state
                    }
                    
                    resp = requests.post(
                        f"{BACKEND_URL}/chat/hiring", 
                        json=payload, 
                        timeout=60
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        assistant_response = data["response"]
                        
                        # Update conversation state
                        st.session_state.conversation_state = data["conversation_state"]
                        
                        # Store candidate info and tech questions if available
                        if data.get("candidate_info"):
                            st.session_state.candidate_info = data["candidate_info"]
                        if data.get("tech_questions"):
                            st.session_state.tech_questions = data["tech_questions"]
                        
                        # Display response with typing effect
                        full_response = ""
                        for chunk in assistant_response.split():
                            full_response += chunk + " "
                            time.sleep(0.02)
                            message_placeholder.markdown(full_response + "▌")
                        message_placeholder.markdown(full_response)
                        
                        # Check if conversation ended
                        if data.get("conversation_ended"):
                            st.session_state.conversation_ended = True
                    else:
                        error_detail = resp.json().get("detail", "Unknown error")
                        full_response = f"❌ Error: {error_detail}"
                        message_placeholder.markdown(full_response)
                        
                except requests.exceptions.ConnectionError:
                    full_response = "❌ Cannot connect to backend. Make sure the backend server is running on port 8000.\\n\\n```bash\\ncd backend && python main.py\\n```"
                    message_placeholder.markdown(full_response)
                except Exception as e:
                    full_response = f"❌ Error: {str(e)}"
                    message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # Auto-save for logged-in users
        if not st.session_state.is_guest:
            save_chat(st.session_state.user_id, st.session_state.current_chat_id, st.session_state.messages)
    
    # Display candidate information sidebar if collected
    if st.session_state.get("candidate_info"):
        with st.sidebar:
            st.markdown("---")
            st.markdown("### Candidate Profile")
            
            info = st.session_state.candidate_info
            if info.get("full_name"):
                st.markdown(f"**Name:** {info['full_name']}")
            if info.get("email"):
                st.markdown(f"**Email:** {info['email']}")
            if info.get("phone"):
                st.markdown(f"**Phone:** {info['phone']}")
            if info.get("years_of_experience"):
                st.markdown(f"**Experience:** {info['years_of_experience']} years")
            if info.get("desired_position"):
                st.markdown(f"**Position:** {info['desired_position']}")
            if info.get("current_location"):
                st.markdown(f"**Location:** {info['current_location']}")
            if info.get("tech_stack"):
                tech_list = info['tech_stack'] if isinstance(info['tech_stack'], list) else [info['tech_stack']]
                st.markdown(f"**Tech Stack:** {', '.join(tech_list)}")



# ============================================================
# ROUTING
# ============================================================
if st.session_state.authenticated:
    show_chat_page()
else:
    show_login_page()
