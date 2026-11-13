"""
tutor_agent.py - EduPath LangGraph Adaptive Tutoring Engine
Implements a stateful multi-turn tutoring agent grounded in OpenStax textbooks.
Features:
- LangGraph state machine with conversational memory window.
- Student misconception detection & dynamic level adaptation (Levels 1, 2, 3).
- Few-shot prompt engineering per pedagogical level.
- RAG grounding with similarity thresholding and autonomous general AI fallback.
"""

import os
import json
from typing import TypedDict, List, Dict, Any, Optional
from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, END
from ingest import search_index

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "openai/gpt-oss-120b"
FAST_MODEL_NAME = "openai/gpt-oss-20b"

def get_groq_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in .env file.")
    return Groq(api_key=GROQ_API_KEY)

# ==========================================
# 1. State Definition
# ==========================================
class TutorState(TypedDict):
    messages: List[Dict[str, str]]             # Sliding window of chat messages
    subject: str                               # "physics", "maths", "biology"
    current_level: int                         # 1 (Foundational), 2 (Conceptual), 3 (Socratic)
    auto_adapt: bool                           # True if level adapts automatically
    detected_misconceptions: List[str]         # Tracked misconceptions
    retrieved_context: str                     # Context text from OpenStax
    citations: List[Dict[str, Any]]            # Page numbers & sources
    rag_score: float                           # Cosine similarity score
    is_fallback: bool                          # True if query was out of OpenStax threshold
    adaptation_reason: str                     # Rationale for why level/style was chosen
    response: str                              # Tutor's final output message

# ==========================================
# 2. Few-Shot Pedagogical Prompt Exemplars
# ==========================================

FEW_SHOT_EXEMPLARS = {
    1: """
### LEVEL 1: FOUNDATIONAL & INTUITIVE (Underserved School / Beginner Level)
**Pedagogical Objective:** Demystify abstract formulas. Build gut-level intuition using vivid real-life physical analogies, simple friendly language, and zero intimidating symbols. Address student misconceptions with warmth.

**Few-Shot Example 1 (Physics - Inertia Misconception):**
- *Student Mistake:* "If an object is moving in space, we must keep applying force or else it stops on its own."
- *Tutor Response:* "That feels intuitive because on Earth, everything slows down due to friction! But imagine sliding across a super smooth ice rink in socks. If nobody pushes you and there's no friction, you'd just keep gliding forever! In deep space, there is no air or ice to slow you down. An object keeps coasting until something bumps into it."

**Few-Shot Example 2 (Maths - Negative Numbers Misconception):**
- *Student Mistake:* "Subtracting a negative number makes things smaller, like 5 - (-3) = 2."
- *Tutor Response:* "Think of your money! A negative number is like a debt or bill you owe someone. If someone walks in and *takes away* (- ) your $3 debt, did you become richer or poorer? You became $3 richer! Taking away a debt adds to your balance: 5 - (-3) = 5 + 3 = 8."
""",

    2: """
### LEVEL 2: CONCEPTUAL & STEP-BY-STEP (Standard High School Level)
**Pedagogical Objective:** Provide structured textbook explanations, standard definitions, formulas, and step-by-step problem-solving. Validate reasoning with formal laws and clear diagrams.

**Few-Shot Example 1 (Physics - Newton's 3rd Law):**
- *Student Mistake:* "Action and reaction forces cancel out to zero, so how can a rocket accelerate?"
- *Tutor Response:* "Action and reaction forces never cancel each other out because they act on **two entirely distinct bodies**.
Let's break down the Free-Body Diagram:
1. The rocket exerts a backward force on the exhaust gas ($F_{rocket \\to gas}$).
2. By Newton's Third Law, the gas exerts an equal and opposite forward force on the rocket ($F_{gas \\to rocket}$).
3. When evaluating the rocket's acceleration, we sum only the forces acting **on the rocket itself**. Hence, $F_{net} = F_{gas \\to rocket} > 0$, driving it forward."

**Few-Shot Example 2 (Maths - Statistics / Standard Deviation):**
- *Student Mistake:* "A higher standard deviation means the data is better."
- *Tutor Response:* "Standard deviation measures **dispersion**, not quality or accuracy.
- Formula: $\\sigma = \\sqrt{\\frac{\\sum (x_i - \\mu)^2}{N}}$
- A high $\\sigma$ indicates values are widely spread out from the mean (high variability).
- A low $\\sigma$ indicates data points cluster tightly around the average."
""",

    3: """
### LEVEL 3: SOCRATIC & CRITICAL INQUIRY (Enriched / AP-Prep Level)
**Pedagogical Objective:** Do not give away answers directly. Probe with thought experiments, boundary conditions, and Socratic questions that force the student to detect their own inconsistencies and apply principles to novel scenarios.

**Few-Shot Example 1 (Physics - Terminal Velocity):**
- *Student Mistake:* "A heavier skydiver will reach infinite speed if they fall long enough."
- *Tutor Response:* "Let's test the boundary conditions of your hypothesis. As the skydiver's velocity $v$ increases, what happens to the aerodynamic drag force $F_d = \\frac{1}{2} \\rho v^2 C_d A$?
Does drag remain constant, or does it grow with the square of speed?
Now, write the equation for net acceleration: $a = \\frac{mg - F_d}{m}$. What happens to $a$ when $F_d$ approaches $mg$? Reflect on whether speed can increase further once net force becomes zero."

**Few-Shot Example 2 (Biology - Photosynthesis & Respiration):**
- *Student Mistake:* "Plants do photosynthesis during the day and don't respire at all."
- *Tutor Response:* "Consider the cellular machinery of an autotroph. While chloroplasts synthesize glucose using photons, which organelle produces ATP for fundamental cellular maintenance when the sun sets? If plants ceased respiration, how would their mitochondria support metabolic active transport?"
"""
}

# ==========================================
# 3. LangGraph Node Functions
# ==========================================

def assess_student_node(state: TutorState) -> Dict[str, Any]:
    """
    Node 1: Evaluates the student's input and chat history.
    Detects conceptual misconceptions and calibrates the pedagogical level.
    """
    client = get_groq_client()
    messages = state.get("messages", [])
    if not messages:
        return {}

    latest_user_msg = messages[-1]["content"] if messages[-1]["role"] == "user" else ""
    current_lvl = state.get("current_level", 2)
    auto_adapt = state.get("auto_adapt", True)

    # History summary (last 4 turns)
    recent_history = messages[-4:-1] if len(messages) > 1 else []
    history_str = "\n".join([f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in recent_history if m.get('content')])

    assessment_prompt = f"""You are an expert pedagogical assessor analyzing a high-school student interaction.
Subject: {state.get('subject', 'science')}
Current Level: {current_lvl} (1: Foundational, 2: Conceptual, 3: Socratic)
Auto-Adapt Enabled: {auto_adapt}

Recent Conversation History:
{history_str}

Latest Student Input:
"{latest_user_msg}"

Tasks:
1. Identify any conceptual misconception, calculation slip, or confusion in the student's input. If none, return null.
2. If Auto-Adapt is TRUE, decide the best difficulty level:
   - Downgrade to Level 1 if student expresses confusion ("I don't get it", "too hard") or shows severe foundational misconceptions.
   - Set to Level 2 for standard questions and regular conceptual inquiries.
   - Upgrade to Level 3 if student shows mastery, asks advanced questions, or seeks deeper challenges.
   If Auto-Adapt is FALSE, keep the level as {current_lvl}.

Return strictly a valid JSON object with these keys:
{{
  "detected_misconception": "string describing misconception or null",
  "recommended_level": 1, 2, or 3,
  "adaptation_reason": "concise explanation of why this style/level was chosen"
}}"""

    try:
        response = client.chat.completions.create(
            model=FAST_MODEL_NAME,
            messages=[{"role": "user", "content": assessment_prompt}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        parsed = json.loads(response.choices[0].message.content)
        
        new_misconceptions = list(state.get("detected_misconceptions", []))
        if parsed.get("detected_misconception"):
            new_misconceptions.append(parsed["detected_misconception"])
            
        new_level = parsed.get("recommended_level", current_lvl) if auto_adapt else current_lvl
        adaptation_reason = parsed.get("adaptation_reason", "Maintaining calibrated difficulty level.")

        return {
            "current_level": new_level,
            "detected_misconceptions": new_misconceptions,
            "adaptation_reason": adaptation_reason
        }
    except Exception as e:
        print(f"Assessment error (using defaults): {e}")
        return {
            "adaptation_reason": "Calibrated for student level."
        }


def retrieve_context_node(state: TutorState) -> Dict[str, Any]:
    """
    Node 2: Queries OpenStax vector index with similarity thresholding.
    If match is below threshold, marks is_fallback=True.
    """
    messages = state.get("messages", [])
    if not messages:
        return {}

    query = messages[-1]["content"]
    subject = state.get("subject", "physics")

    try:
        results, is_grounded, top_score = search_index(
            query=query,
            subject=subject,
            top_k=3,
            threshold=0.32
        )

        context_texts = []
        citations = []
        for r in results:
            c = r["chunk"]
            context_texts.append(f"[OpenStax {c['source']} | Page {c['page']}]\n{c['text']}")
            citations.append({
                "source": c["source"],
                "page": c["page"],
                "score": round(r["score"], 3)
            })

        retrieved_context = "\n\n---\n\n".join(context_texts) if is_grounded else ""

        return {
            "retrieved_context": retrieved_context,
            "citations": citations if is_grounded else [],
            "rag_score": round(top_score, 3),
            "is_fallback": not is_grounded
        }
    except Exception as e:
        print(f"Retrieval error: {e}")
        return {
            "retrieved_context": "",
            "citations": [],
            "rag_score": 0.0,
            "is_fallback": True
        }


def generate_adaptive_response_node(state: TutorState) -> Dict[str, Any]:
    """
    Node 3: Generates the pedagogical response using few-shot exemplars,
    calibrated to current_level and grounded in OpenStax context (or fallback).
    """
    client = get_groq_client()
    messages = state.get("messages", [])
    level = state.get("current_level", 2)
    subject = state.get("subject", "physics")
    is_fallback = state.get("is_fallback", False)
    retrieved_context = state.get("retrieved_context", "")
    misconceptions = state.get("detected_misconceptions", [])
    
    # Grounding instructions
    if is_fallback or not retrieved_context:
        grounding_instruction = """
[FALLBACK MODE - GENERAL AI KNOWLEDGE]
The student asked a query outside current OpenStax chapter boundaries.
Provide a pedagogically sound explanation using general scientific knowledge, maintaining accuracy.
"""
    else:
        grounding_instruction = f"""
[OPENSTAX GROUNDED KNOWLEDGE BASE]
Strictly ground definitions, terminology, and core facts on the verified OpenStax textbook material below:
{retrieved_context}
"""

    # Active misconception context
    misconception_instruction = ""
    if misconceptions:
        recent_misc = misconceptions[-2:]
        misconception_instruction = f"""
Active Misconceptions Detected for this Student:
{chr(10).join(['- ' + m for m in recent_misc])}
Explicitly help the student unlearn these specific misconceptions in your explanation.
"""

    level_exemplar = FEW_SHOT_EXEMPLARS.get(level, FEW_SHOT_EXEMPLARS[2])

    formatting_rules = (
        "Important Rules:\n"
        "- Stay warmly encouraging, empathetic, and patient.\n"
        "- Structure your response cleanly with clear numbered sections, bold terms, and readable bullet points.\n"
        "- MATH FORMATTING: Always use single dollar signs $...$ for inline math (e.g. $F = ma$). Always use double dollar signs $$...$$ on their own line for block math. Never use raw square brackets [...] for math equations.\n"
        "- AVOID RAW PIPE TABLES: Do NOT use markdown pipe tables (| ... |). Instead, present comparisons and summaries using structured bullet points with bold titles (e.g. • **Misconception:** ... \\n  - *Why it's wrong:* ... \\n  - *Correct view:* ...). Bullet points render 100x cleaner on all screens.\n"
        "- Never overwhelm Level 1 with dense symbols. Never spoonfeed Level 3 with direct answers."
    )

    system_prompt = f"""You are EduPath, an AI personalized tutor designed for underserved school students (UN SDG 4: Quality Education).
Your primary role is to adapt your explanation style strictly to the student's assigned difficulty level.

Subject: {subject.upper()}
Active Target Level: LEVEL {level}

{level_exemplar}

{grounding_instruction}

{misconception_instruction}

{formatting_rules}
"""

    # Sliding context window (last 6 messages)
    chat_history = []
    for msg in messages[-6:]:
        c = msg.get("content", "")
        if c:
            chat_history.append({"role": msg.get("role", "user"), "content": c})

    llm_messages = [{"role": "system", "content": system_prompt}] + chat_history

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=llm_messages,
            temperature=0.4,
            max_tokens=2500
        )
        tutor_response = response.choices[0].message.content
    except Exception as e:
        print(f"Primary model error, using fallback model: {e}")
        response = client.chat.completions.create(
            model=FAST_MODEL_NAME,
            messages=llm_messages,
            temperature=0.4,
            max_tokens=2500
        )
        tutor_response = response.choices[0].message.content

    return {
        "response": tutor_response
    }

# ==========================================
# 4. Build LangGraph Workflow
# ==========================================

def build_tutor_graph():
    """
    Constructs the LangGraph state machine:
    Assess Student -> Retrieve Context -> Generate Adaptive Response -> END
    """
    workflow = StateGraph(TutorState)
    
    workflow.add_node("assess_student", assess_student_node)
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("generate_response", generate_adaptive_response_node)
    
    workflow.set_entry_point("assess_student")
    workflow.add_edge("assess_student", "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()

# Instantiate compiled app
tutor_graph_app = build_tutor_graph()

# ==========================================
# 5. Multi-Level Comparison Showcase Helper
# ==========================================

def generate_multilevel_comparison(query: str, subject: str = "physics") -> Dict[int, Dict[str, Any]]:
    """
    Generates Level 1, Level 2, and Level 3 explanations for the SAME question.
    Fulfills the primary teacher deliverable for evaluation.
    """
    # Retrieve context once
    results, is_grounded, top_score = search_index(query=query, subject=subject, top_k=3, threshold=0.32)
    citations = [{"source": r["chunk"]["source"], "page": r["chunk"]["page"], "score": round(r["score"], 3)} for r in results] if is_grounded else []
    retrieved_context = "\n\n".join([f"[{r['chunk']['source']} p.{r['chunk']['page']}]\n{r['chunk']['text']}" for r in results]) if is_grounded else ""

    comparison = {}
    
    for lvl in [1, 2, 3]:
        dummy_state: TutorState = {
            "messages": [{"role": "user", "content": query}],
            "subject": subject,
            "current_level": lvl,
            "auto_adapt": False,
            "detected_misconceptions": [],
            "retrieved_context": retrieved_context,
            "citations": citations,
            "rag_score": round(top_score, 3),
            "is_fallback": not is_grounded,
            "adaptation_reason": f"Demonstrating Level {lvl} pedagogy.",
            "response": ""
        }
        output = generate_adaptive_response_node(dummy_state)
        comparison[lvl] = {
            "level": lvl,
            "response": output["response"],
            "citations": citations,
            "rag_score": round(top_score, 3),
            "is_fallback": not is_grounded
        }
        
    return comparison
