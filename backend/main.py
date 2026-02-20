from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Optional, Dict, Any
import json
import base64
import io
import os

from document_loader import DocumentLoader
from template_prompt import get_resume_prompt, get_jd_prompt
from conversation_manager import ConversationManager, ConversationState
from hiring_prompts import (
    get_greeting_prompt, 
    get_info_extraction_prompt,
    get_tech_questions_prompt,
    get_conversation_response_prompt,
    get_fallback_prompt,
    detect_conversation_ending,
    get_conclusion_message
)
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
app = FastAPI(
    title="TalentScout Assistant API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FileInput(BaseModel):
    fileName: str
    fileContent: str  


class ChatRequest(BaseModel):
    message: str
    conversation_state: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    conversation_state: Dict[str, Any]
    candidate_info: Optional[Dict[str, Any]] = None
    tech_questions: Optional[Dict[str, Any]] = None
    stage: str
    conversation_ended: bool = False


def get_llm(temperature: float = 0):
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        groq_api_key=api_key
    )


def parse_with_llm(text: str, prompt: str) -> dict:
    try:
        llm = get_llm()
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        return json.loads(response_text)
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse response: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing: {str(e)}"
        )


def get_llm_response(prompt: str, temperature: float = 0.7) -> str:
    try:
        llm = get_llm(temperature=temperature)
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting response: {str(e)}"
        )


@app.get("/")
async def root():
    return {
        "status": "online",
        "endpoints": ["/chat/hiring", "/parse/resume", "/parse/jd"]
    }


@app.post("/chat/hiring", response_model=ChatResponse)
async def chat_hiring(request: ChatRequest):
    try:
        if request.conversation_state:
            state = ConversationManager.restore_conversation(request.conversation_state)
        else:
            state = ConversationManager.initialize_conversation()
        
        user_message = request.message.strip()
        state.add_message("user", user_message)
        
        if detect_conversation_ending(user_message):
            conclusion_msg = get_conclusion_message(state.candidate_info.get("full_name"))
            state.add_message("assistant", conclusion_msg)
            state.stage = "conclusion"
            
            return ChatResponse(
                response=conclusion_msg,
                conversation_state=state.to_dict(),
                candidate_info=state.candidate_info,
                tech_questions=state.tech_questions,
                stage=state.stage,
                conversation_ended=True
            )
        
        action = ConversationManager.determine_next_action(state, user_message)
        assistant_response = ""
        
        if action == "greet":
            greeting_prompt = get_greeting_prompt()
            assistant_response = get_llm_response(greeting_prompt, temperature=0.7)
            state.stage = "info_gathering"
            state.advance_stage()
        
        elif action == "extract_info":
            extraction_prompt = get_info_extraction_prompt(
                user_message, 
                state.get_conversation_history_text()
            )
            
            try:
                extracted_info = parse_with_llm(user_message, extraction_prompt)
                if extracted_info:
                    state.update_candidate_info(extracted_info)
            except Exception as e:
                print(f"Extraction error: {e}")
            
            response_prompt = get_conversation_response_prompt(
                user_message,
                state.get_conversation_history_text(),
                state.candidate_info,
                state.stage
            )
            assistant_response = get_llm_response(response_prompt, temperature=0.7)
        
        elif action == "generate_questions":
            tech_stack = state.candidate_info.get("tech_stack", [])
            
            if tech_stack:
                questions_prompt = get_tech_questions_prompt(tech_stack)
                
                try:
                    tech_questions = parse_with_llm("", questions_prompt)
                    state.set_tech_questions(tech_questions)
                    
                    assistant_response = f"I've prepared some technical questions for your skills in {', '.join(tech_stack)}.\n\n"
                    assistant_response += ConversationManager.format_tech_questions_display(tech_questions)
                    
                    state.stage = "tech_questions"
                    
                except Exception as e:
                    assistant_response = "I'll prepare some questions for you shortly."
                    print(f"Generation error: {e}")
            else:
                assistant_response = "Could you list your tech stack?"
        
        elif action == "respond":
            response_prompt = get_conversation_response_prompt(
                user_message,
                state.get_conversation_history_text(),
                state.candidate_info,
                state.stage
            )
            assistant_response = get_llm_response(response_prompt, temperature=0.7)
        
        elif action == "conclude":
            conclusion_msg = get_conclusion_message(state.candidate_info.get("full_name"))
            assistant_response = conclusion_msg
            state.stage = "conclusion"
        
        else:
            fallback_prompt = get_fallback_prompt(user_message)
            assistant_response = get_llm_response(fallback_prompt, temperature=0.7)
        
        state.add_message("assistant", assistant_response)
        
        return ChatResponse(
            response=assistant_response,
            conversation_state=state.to_dict(),
            candidate_info=state.candidate_info,
            tech_questions=state.tech_questions,
            stage=state.stage,
            conversation_ended=(state.stage == "conclusion")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@app.post("/parse/resume")
async def parse_resume(file_input: FileInput):
    try:
        file_bytes = base64.b64decode(file_input.fileContent)
        file_stream = io.BytesIO(file_bytes)
        text = DocumentLoader.process_file(file_stream, file_input.fileName)
        
        if not text:
            raise HTTPException(
                status_code=400,
                detail="Empty text"
            )
        
        prompt = get_resume_prompt(text)
        parsed_data = parse_with_llm(text, prompt)
        return JSONResponse(content=parsed_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/parse/jd")
async def parse_jd(file_input: FileInput):
    try:
        file_bytes = base64.b64decode(file_input.fileContent)
        file_stream = io.BytesIO(file_bytes)
        text = DocumentLoader.process_file(file_stream, file_input.fileName)
        
        if not text:
            raise HTTPException(
                status_code=400,
                detail="Empty text"
            )
        
        prompt = get_jd_prompt(text)
        parsed_data = parse_with_llm(text, prompt)
        return JSONResponse(content=parsed_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
