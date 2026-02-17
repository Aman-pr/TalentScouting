def get_greeting_prompt() -> str:
    """Returns the initial greeting message for candidates."""
    return """You are an AI Hiring Assistant for TalentScout, a recruitment agency specializing in technology placements.

Your objective is to conduct an initial candidate screening interview. You will:
1. Collect essential candidate information (name, contact details, experience, desired position, location, and technical skills)
2. Generate relevant technical questions based on their declared tech stack
3. Maintain a professional, conversational tone throughout the interaction

Start by greeting the candidate professionally and clearly explaining:
- That you are TalentScout's AI Hiring Assistant
- Your purpose is to conduct an initial screening interview
- You will be collecting their information and asking technical questions
- The process will take approximately 5-10 minutes

Keep your greeting professional, clear, and concise (3-4 sentences). Do not use emojis."""


def get_info_extraction_prompt(user_message: str, conversation_history: str) -> str:
    """
    Extract candidate information from their message and return structured JSON.
    """
    return f"""You are an AI assistant helping to extract candidate information from a conversation.

CONVERSATION HISTORY:
{conversation_history}

LATEST USER MESSAGE:
{user_message}

Extract any of the following information that is present in the user's message:
- full_name: The candidate's full name
- email: Email address
- phone: Phone number
- years_of_experience: Number of years of professional experience (as a number)
- desired_position: Job position(s) they're interested in
- current_location: City, state, or country where they're located
- tech_stack: List of technologies, programming languages, frameworks, databases, tools they know

Return ONLY a JSON object with the fields that were found. Use null for fields not mentioned.
If the user is just greeting or asking questions, return an empty object {{}}.

Example output format:
{{
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "years_of_experience": 5,
    "desired_position": "Senior Software Engineer",
    "current_location": "San Francisco, CA",
    "tech_stack": ["Python", "Django", "React", "PostgreSQL", "AWS"]
}}

JSON OUTPUT:"""


def get_tech_questions_prompt(tech_stack: list) -> str:
    """
    Generate technical questions based on the candidate's tech stack.
    """
    tech_list = ", ".join(tech_stack)
    
    return f"""You are a technical interviewer for TalentScout. Generate relevant technical questions to assess a candidate's proficiency.

CANDIDATE'S TECH STACK: {tech_list}

For each technology in the tech stack, generate 3-5 technical questions that:
- Range from intermediate to advanced difficulty
- Cover practical, real-world scenarios
- Test both theoretical knowledge and practical application
- Are specific to that technology (not generic programming questions)

Return a JSON object where each key is a technology and the value is a list of questions.

Example format:
{{
    "Python": [
        "Explain the difference between list comprehensions and generator expressions. When would you use each?",
        "How does Python's Global Interpreter Lock (GIL) affect multi-threaded applications?",
        "Describe how you would implement a decorator that caches function results."
    ],
    "Django": [
        "Explain Django's ORM and how it prevents SQL injection attacks.",
        "How would you optimize a Django application that's experiencing slow database queries?",
        "Describe the difference between Django's select_related and prefetch_related."
    ]
}}

Generate questions for: {tech_list}

JSON OUTPUT:"""


def get_conversation_response_prompt(user_message: str, conversation_history: str, candidate_info: dict, stage: str) -> str:
    """
    Generate contextual responses based on conversation stage and collected information.
    """
    missing_fields = []
    if not candidate_info.get("full_name"):
        missing_fields.append("full name")
    if not candidate_info.get("email"):
        missing_fields.append("email address")
    if not candidate_info.get("phone"):
        missing_fields.append("phone number")
    if not candidate_info.get("years_of_experience"):
        missing_fields.append("years of experience")
    if not candidate_info.get("desired_position"):
        missing_fields.append("desired position")
    if not candidate_info.get("current_location"):
        missing_fields.append("current location")
    if not candidate_info.get("tech_stack"):
        missing_fields.append("tech stack")
    
    context = f"""You are an AI Hiring Assistant for TalentScout.

CONVERSATION STAGE: {stage}

CONVERSATION HISTORY:
{conversation_history}

LATEST USER MESSAGE:
{user_message}

COLLECTED CANDIDATE INFORMATION:
{candidate_info}

MISSING INFORMATION: {', '.join(missing_fields) if missing_fields else 'None - all information collected'}
"""

    if stage == "greeting":
        context += """
The candidate has just started the conversation. Greet them warmly and explain that you'll be collecting some information for the initial screening process. Keep it brief and friendly."""
    
    elif stage == "info_gathering":
        if missing_fields:
            context += f"""
You are collecting candidate information. You still need: {', '.join(missing_fields)}.

Ask for the missing information in a natural, conversational way. Don't ask for everything at once - ask for 1-2 items at a time.
Be friendly and professional. If the user provided some information, acknowledge it before asking for more."""
        else:
            context += """
All candidate information has been collected! Thank them and ask them to list their tech stack (programming languages, frameworks, databases, tools they're proficient in).
If tech stack is already provided, acknowledge it and let them know you'll be asking some technical questions."""
    
    elif stage == "tech_questions":
        context += """
You have the candidate's tech stack and have generated technical questions. 
Engage with their answers, provide brief feedback if appropriate, and ask follow-up questions naturally.
Maintain a professional but friendly tone."""
    
    elif stage == "conclusion":
        context += """
The conversation is concluding. Thank the candidate for their time, summarize what was discussed, 
and explain that the TalentScout team will review their information and reach out within 3-5 business days.
Be warm and professional."""
    
    context += """

Generate a natural, conversational response. Keep it concise (2-4 sentences unless more detail is needed).
Do not ask for information that has already been provided.

RESPONSE:"""
    
    return context


def get_fallback_prompt(user_message: str) -> str:
    """
    Handle unexpected or off-topic inputs.
    """
    return f"""You are an AI Hiring Assistant for TalentScout. The candidate said something unexpected or off-topic.

USER MESSAGE: {user_message}

Politely redirect the conversation back to the hiring process. Remind them that you're here to help with their job application.
If they seem confused, briefly re-explain what information you need.
If they're asking about the company or process, provide a brief, helpful answer and then redirect.

Keep your response professional, helpful, and brief (2-3 sentences).

RESPONSE:"""


def detect_conversation_ending(user_message: str) -> bool:
    """
    Detect if the user wants to end the conversation.
    """
    ending_keywords = [
        "bye", "goodbye", "exit", "quit", "end", "stop", 
        "that's all", "thats all", "no more", "done", "finish"
    ]
    
    message_lower = user_message.lower().strip()
    
    for keyword in ending_keywords:
        if keyword == message_lower or (len(message_lower.split()) <= 3 and keyword in message_lower):
            return True
    return False


def get_conclusion_message(candidate_name: str = "there") -> str:
    """
    Generate a conclusion message when the conversation ends.
    """
    name_part = f"{candidate_name}" if candidate_name and candidate_name != "there" else "there"
    
    return f"""Thank you for your time, {name_part}.

I have collected all the necessary information for your initial screening. Our TalentScout recruitment team will carefully review your profile and technical responses.

You can expect to hear back from us within 3-5 business days via the email address you provided. If your profile matches our current openings, we will reach out to schedule a detailed interview.

Best of luck with your job search."""
