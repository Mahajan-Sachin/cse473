"""
server.py - EduPath FastAPI Backend
Exposes clean REST APIs for the React frontend, orchestrating the LangGraph
adaptive tutor engine, ChromaDB retrieval, and multi-level response generation.
"""

import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import concurrent.futures

from tutor_agent import (
    tutor_graph_app,
    generate_adaptive_response_node,
    assess_student_node,
    retrieve_context_node,
    TutorState,
    search_index
)

load_dotenv()

app = FastAPI(title="EduPath API", version="2.0")

# Enable CORS for React frontend (Vite defaults to port 5173 / 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    subject: str = "physics"
    current_level: int = 1
    auto_adapt: bool = True
    history: List[Dict[str, str]] = []
    detected_misconceptions: List[str] = []

class LevelResponse(BaseModel):
    text: str
    citations: List[Dict[str, Any]]
    rag_score: float
    is_fallback: bool

class ChatResponse(BaseModel):
    primary_level: int
    adaptation_reason: str
    detected_misconceptions: List[str]
    citations: List[Dict[str, Any]]
    rag_score: float
    is_fallback: bool
    levels: Dict[int, LevelResponse]

@app.get("/api/health")
def health_check():
    return {"status": "ok", "agent": "EduPath LangGraph Agent", "model": "openai/gpt-oss-120b"}

@app.get("/api/subjects")
def get_subjects():
    return {
        "subjects": [
            {
                "id": "physics",
                "name": "NCERT Physics (Class 11 & 12)",
                "icon": "Atom",
                "badge": "NCERT Physics (Classes XI & XII)",
                "sample_questions": [
                    "Why do heavier objects fall at the same speed as light objects in a vacuum?",
                    "If a horse pulls on a cart, why does the cart move if action and reaction forces are equal?",
                    "What is the difference between acceleration and gravity according to NCERT?"
                ]
            },
            {
                "id": "chemistry",
                "name": "NCERT Chemistry (Class 11 & 12)",
                "icon": "FlaskConical",
                "badge": "NCERT Chemistry (Classes XI & XII)",
                "sample_questions": [
                    "Why does ice float on water? Explain via hydrogen bonding.",
                    "What is the difference between molarity and molality, and which is temperature independent?",
                    "Explain Le Chatelier's principle with an intuitive analogy."
                ]
            },
            {
                "id": "maths",
                "name": "NCERT Mathematics (Class 11 & 12)",
                "icon": "Sigma",
                "badge": "NCERT Mathematics (Classes XI & XII)",
                "sample_questions": [
                    "What is standard deviation and what does it tell us about data?",
                    "Can the probability of an event ever be greater than 1 or negative?",
                    "Why is dividing by zero undefined in mathematics?"
                ]
            }
        ]
    }

@app.post("/api/chat", response_model=ChatResponse)
def handle_chat(payload: ChatRequest):
    """
    Processes student query:
    1. Runs student assessment to detect misconceptions and calibrate level.
    2. Retrieves OpenStax context from ChromaDB with similarity thresholding.
    3. Concurrently generates Level 1, Level 2, and Level 3 explanations so user
       can toggle between them instantly without waiting or reloading.
    """
    try:
        clean_messages = []
        for h in payload.history:
            role = h.get("role", "user")
            content = h.get("content", "")
            if content and str(content).strip():
                clean_messages.append({"role": role, "content": str(content)})
        clean_messages.append({"role": "user", "content": payload.message})

        messages = clean_messages
        
        # 1. State for assessment & retrieval
        initial_state: TutorState = {
            "messages": messages,
            "subject": payload.subject,
            "current_level": payload.current_level,
            "auto_adapt": payload.auto_adapt,
            "detected_misconceptions": payload.detected_misconceptions,
            "retrieved_context": "",
            "citations": [],
            "rag_score": 0.0,
            "is_fallback": False,
            "adaptation_reason": "",
            "response": ""
        }
        
        # Assess student (detect misconceptions & determine active level)
        assess_update = assess_student_node(initial_state)
        active_level = assess_update.get("current_level", payload.current_level)
        misconceptions = assess_update.get("detected_misconceptions", payload.detected_misconceptions)
        adaptation_reason = assess_update.get("adaptation_reason", "Calibrated for student level.")
        
        initial_state["current_level"] = active_level
        initial_state["detected_misconceptions"] = misconceptions
        
        # Retrieve context from ChromaDB
        retrieval_update = retrieve_context_node(initial_state)
        retrieved_context = retrieval_update.get("retrieved_context", "")
        citations = retrieval_update.get("citations", [])
        rag_score = retrieval_update.get("rag_score", 0.0)
        is_fallback = retrieval_update.get("is_fallback", False)
        
        # 2. Concurrently generate L1, L2, L3 responses so switching is instant
        def generate_for_level(lvl: int) -> tuple:
            state_for_lvl: TutorState = {
                "messages": messages,
                "subject": payload.subject,
                "current_level": lvl,
                "auto_adapt": False,
                "detected_misconceptions": misconceptions,
                "retrieved_context": retrieved_context,
                "citations": citations,
                "rag_score": rag_score,
                "is_fallback": is_fallback,
                "adaptation_reason": f"Level {lvl} pedagogical style.",
                "response": ""
            }
            res = generate_adaptive_response_node(state_for_lvl)
            return lvl, res.get("response", "")

        levels_dict = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(generate_for_level, lvl) for lvl in [1, 2, 3]]
            for future in concurrent.futures.as_completed(futures):
                lvl, text = future.result()
                levels_dict[lvl] = LevelResponse(
                    text=text,
                    citations=citations,
                    rag_score=rag_score,
                    is_fallback=is_fallback
                )

        return ChatResponse(
            primary_level=active_level,
            adaptation_reason=adaptation_reason,
            detected_misconceptions=misconceptions,
            citations=citations,
            rag_score=rag_score,
            is_fallback=is_fallback,
            levels=levels_dict
        )

    except Exception as e:
        print(f"Server error during chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

