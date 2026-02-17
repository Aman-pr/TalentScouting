"""
Conversation state manager for the hiring assistant chatbot.
Tracks conversation stage, collected information, and manages conversation flow.
"""

from typing import Dict, List, Optional
from enum import Enum
import json


class ConversationStage(str, Enum):
    """Stages of the hiring conversation."""
    GREETING = "greeting"
    INFO_GATHERING = "info_gathering"
    TECH_QUESTIONS = "tech_questions"
    CONCLUSION = "conclusion"


class ConversationState:
    """
    Manages the state of a hiring conversation.
    Tracks collected information, conversation stage, and history.
    """
    
    def __init__(self, state_dict: Optional[Dict] = None):
        """
        Initialize conversation state from a dictionary or create new.
        """
        if state_dict:
            self.stage = state_dict.get("stage", ConversationStage.GREETING)
            self.candidate_info = state_dict.get("candidate_info", {})
            self.tech_questions = state_dict.get("tech_questions", {})
            self.conversation_history = state_dict.get("conversation_history", [])
            self.questions_asked = state_dict.get("questions_asked", [])
        else:
            self.stage = ConversationStage.GREETING
            self.candidate_info = {
                "full_name": None,
                "email": None,
                "phone": None,
                "years_of_experience": None,
                "desired_position": None,
                "current_location": None,
                "tech_stack": None
            }
            self.tech_questions = {}
            self.conversation_history = []
            self.questions_asked = []
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary for serialization."""
        return {
            "stage": self.stage,
            "candidate_info": self.candidate_info,
            "tech_questions": self.tech_questions,
            "conversation_history": self.conversation_history,
            "questions_asked": self.questions_asked
        }
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def get_conversation_history_text(self) -> str:
        """Get the last 10 messages from conversation history as formatted text."""
        if not self.conversation_history:
            return "No previous messages."
        
        history_text = []
        for msg in self.conversation_history[-10:]:
            role = "Assistant" if msg["role"] == "assistant" else "Candidate"
            history_text.append(f"{role}: {msg['content']}")
        
        return "\n".join(history_text)
    
    def update_candidate_info(self, extracted_info: Dict):
        """
        Update candidate information with newly extracted data.
        """
        for key, value in extracted_info.items():
            if value is not None and key in self.candidate_info:
                # For tech_stack, merge lists if both exist
                if key == "tech_stack" and self.candidate_info[key]:
                    existing = self.candidate_info[key] if isinstance(self.candidate_info[key], list) else []
                    new_items = value if isinstance(value, list) else [value]
                    # Merge and remove duplicates
                    self.candidate_info[key] = list(set(existing + new_items))
                else:
                    self.candidate_info[key] = value
    
    def is_info_complete(self) -> bool:
        """Check if all required candidate information has been collected."""
        required_fields = ["full_name", "email", "phone", "years_of_experience", 
                          "desired_position", "current_location", "tech_stack"]
        
        for field in required_fields:
            if not self.candidate_info.get(field):
                return False
        return True
    
    def get_missing_fields(self) -> List[str]:
        """Get list of missing required fields."""
        required_fields = {
            "full_name": "full name",
            "email": "email address",
            "phone": "phone number",
            "years_of_experience": "years of experience",
            "desired_position": "desired position",
            "current_location": "current location",
            "tech_stack": "tech stack"
        }
        
        missing = []
        for field, display_name in required_fields.items():
            if not self.candidate_info.get(field):
                missing.append(display_name)
        return missing
    
    def set_tech_questions(self, questions: Dict[str, List[str]]):
        """Store generated technical questions."""
        self.tech_questions = questions
    
    def advance_stage(self):
        """Move to the next conversation stage."""
        stage_order = [
            ConversationStage.GREETING,
            ConversationStage.INFO_GATHERING,
            ConversationStage.TECH_QUESTIONS,
            ConversationStage.CONCLUSION
        ]
        
        current_index = stage_order.index(self.stage)
        if current_index < len(stage_order) - 1:
            self.stage = stage_order[current_index + 1]
    
    def should_advance_to_tech_questions(self) -> bool:
        """
        Check if we should move to technical questions stage.
        """
        return (self.stage == ConversationStage.INFO_GATHERING and 
                self.is_info_complete() and 
                self.candidate_info.get("tech_stack") and
                not self.tech_questions)
    
    def get_summary(self) -> Dict:
        """Get a summary of the conversation state for display."""
        return {
            "stage": self.stage,
            "info_complete": self.is_info_complete(),
            "missing_fields": self.get_missing_fields(),
            "tech_stack": self.candidate_info.get("tech_stack", []),
            "questions_generated": len(self.tech_questions) > 0,
            "total_messages": len(self.conversation_history)
        }


class ConversationManager:
    """
    Manages conversation flow and state transitions.
    """
    
    @staticmethod
    def initialize_conversation() -> ConversationState:
        """Create a new conversation state."""
        return ConversationState()
    
    @staticmethod
    def restore_conversation(state_dict: Dict) -> ConversationState:
        """Restore conversation state from dictionary."""
        return ConversationState(state_dict)
    
    @staticmethod
    def determine_next_action(state: ConversationState, user_message: str) -> str:
        """
        Determine what action to take based on current state and user message.
        
        Returns:
            Action to take: 'greet', 'extract_info', 'generate_questions', 
                           'respond', 'conclude'
        """
        from hiring_prompts import detect_conversation_ending
        
        # Check if user wants to end conversation
        if detect_conversation_ending(user_message):
            return "conclude"
        
        # First message - greet
        if state.stage == ConversationStage.GREETING and len(state.conversation_history) == 0:
            return "greet"
        
        # Gathering information
        if state.stage == ConversationStage.INFO_GATHERING:
            if state.should_advance_to_tech_questions():
                return "generate_questions"
            else:
                return "extract_info"
        
        # In tech questions stage
        if state.stage == ConversationStage.TECH_QUESTIONS:
            return "respond"
        
        # Default: respond contextually
        return "respond"
    
    @staticmethod
    def format_candidate_info_display(candidate_info: Dict) -> str:
        """
        Format candidate information for display.
        
        Args:
            candidate_info: Dictionary of candidate information
            
        Returns:
            Formatted string for display
        """
        lines = ["**📋 Collected Information:**\n"]
        
        field_labels = {
            "full_name": "👤 Name",
            "email": "📧 Email",
            "phone": "📱 Phone",
            "years_of_experience": "💼 Experience",
            "desired_position": "🎯 Position",
            "current_location": "📍 Location",
            "tech_stack": "💻 Tech Stack"
        }
        
        for field, label in field_labels.items():
            value = candidate_info.get(field)
            if value:
                if field == "years_of_experience":
                    display_value = f"{value} years"
                elif field == "tech_stack":
                    if isinstance(value, list):
                        display_value = ", ".join(value)
                    else:
                        display_value = value
                else:
                    display_value = value
                
                lines.append(f"- {label}: {display_value}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_tech_questions_display(tech_questions: Dict[str, List[str]]) -> str:
        """
        Format technical questions for display.
        
        Args:
            tech_questions: Dictionary mapping technology to questions
            
        Returns:
            Formatted string for display
        """
        if not tech_questions:
            return ""
        
        lines = ["**❓ Technical Questions:**\n"]
        
        for tech, questions in tech_questions.items():
            lines.append(f"\n**{tech}:**")
            for i, question in enumerate(questions, 1):
                lines.append(f"{i}. {question}")
        
        return "\n".join(lines)
