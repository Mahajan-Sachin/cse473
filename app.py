"""
app.py - EduPath Interactive Web Application
Built with Streamlit & LangGraph for CSE 473 (Google Solution Challenge - SDG 4).
Features:
1. 💬 1-on-1 Interactive Adaptive Tutoring Chat with live memory window.
2. 📊 Multi-Level Comparison Matrix (Side-by-side Level 1, 2, 3 generation).
3. 🧠 Live Agent Inspector (RAG scores, fallback flag, detected misconceptions, pedagogical rationale).
"""

import streamlit as st
import time
from tutor_agent import tutor_graph_app, generate_multilevel_comparison

# ==========================================
# Page Configuration & Aesthetics
# ==========================================
st.set_page_config(
    page_title="EduPath - Personalized Tutoring Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished educational interface
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 8px;
    }
    .badge-sdg { background-color: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; }
    .badge-google { background-color: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
    .badge-openstax { background-color: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; }
    .badge-langgraph { background-color: #F3E8FF; color: #6B21A8; border: 1px solid #E9D5FF; }

    .inspector-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    
    .level-badge-1 { background-color: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; font-weight: 600; padding: 3px 8px; border-radius: 6px; }
    .level-badge-2 { background-color: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; font-weight: 600; padding: 3px 8px; border-radius: 6px; }
    .level-badge-3 { background-color: #FAF5FF; color: #7E22CE; border: 1px solid #E9D5FF; font-weight: 600; padding: 3px 8px; border-radius: 6px; }
    
    .misconception-box {
        background-color: #FFF1F2;
        border-left: 4px solid #E11D48;
        padding: 8px 12px;
        border-radius: 4px;
        margin: 6px 0;
        font-size: 0.85rem;
        color: #9F1239;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# Session State Initialization
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "subject" not in st.session_state:
    st.session_state.subject = "physics"

if "current_level" not in st.session_state:
    st.session_state.current_level = 2

if "auto_adapt" not in st.session_state:
    st.session_state.auto_adapt = True

if "detected_misconceptions" not in st.session_state:
    st.session_state.detected_misconceptions = []

if "last_inspector" not in st.session_state:
    st.session_state.last_inspector = {
        "rag_score": 0.0,
        "is_fallback": False,
        "citations": [],
        "adaptation_reason": "System initialized. Ready for student inquiry."
    }

# ==========================================
# Sidebar: Agent Controls & Inspector
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ Tutor Control Panel")
    
    # 1. Subject Selector
    selected_subject = st.selectbox(
        "📚 Target STEM Subject",
        options=["physics", "maths", "biology"],
        format_func=lambda s: {
            "physics": "⚛️ High School Physics",
            "maths": "📐 High School Statistics / Maths",
            "biology": "🧬 Concepts of Biology"
        }.get(s, s),
        index=["physics", "maths", "biology"].index(st.session_state.subject)
    )
    if selected_subject != st.session_state.subject:
        st.session_state.subject = selected_subject
        st.session_state.messages = []
        st.rerun()

    # 2. Adaptation Mode
    st.markdown("---")
    st.markdown("#### 🎯 Pedagogical Level Mode")
    adapt_mode = st.radio(
        "Adaptation Strategy:",
        options=["⚡ Auto-Adaptive (AI adjusts to student)", "🎚️ Manual Lock (For testing/viva demo)"]
    )
    is_auto = "Auto-Adaptive" in adapt_mode
    st.session_state.auto_adapt = is_auto

    if not is_auto:
        manual_lvl = st.select_slider(
            "Select Fixed Difficulty Level:",
            options=[1, 2, 3],
            value=st.session_state.current_level,
            format_func=lambda x: {
                1: "Level 1: Foundational (Analogies)",
                2: "Level 2: Conceptual (Standard)",
                3: "Level 3: Socratic (Critical Thinking)"
            }[x]
        )
        st.session_state.current_level = manual_lvl

    # 3. Live State Inspector
    st.markdown("---")
    st.markdown("### 🔍 Live Agent State Inspector")
    
    lvl_names = {
        1: ("Level 1: Foundational", "level-badge-1"),
        2: ("Level 2: Conceptual", "level-badge-2"),
        3: ("Level 3: Socratic Inquiry", "level-badge-3")
    }
    lvl_label, lvl_css = lvl_names.get(st.session_state.current_level, ("Level 2", "level-badge-2"))
    st.markdown(f"**Active Level:** <span class='{lvl_css}'>{lvl_label}</span>", unsafe_allow_html=True)
    
    # Grounding Status Badge
    insp = st.session_state.last_inspector
    if insp["is_fallback"]:
        st.markdown("**Source Grounding:** <span style='color:#D97706; font-weight:600;'>⚡ Autonomous Fallback (General AI)</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"**Source Grounding:** <span style='color:#16A34A; font-weight:600;'>📖 OpenStax Grounded (Score: {insp['rag_score']})</span>", unsafe_allow_html=True)

    st.markdown(f"**Adaptation Rationale:**\n*{insp['adaptation_reason']}*")

    # Misconceptions Tracker
    st.markdown("---")
    st.markdown("#### 🚨 Tracked Student Misconceptions")
    if st.session_state.detected_misconceptions:
        for m in reversed(st.session_state.detected_misconceptions[-4:]):
            st.markdown(f"<div class='misconception-box'>⚠️ {m}</div>", unsafe_allow_html=True)
    else:
        st.caption("No misconceptions detected yet. Ready to assist!")

    # Reset Button
    st.markdown("---")
    if st.button("🗑️ Reset Chat & Memory", use_container_width=True):
        st.session_state.messages = []
        st.session_state.detected_misconceptions = []
        st.session_state.current_level = 2
        st.session_state.last_inspector = {
            "rag_score": 0.0,
            "is_fallback": False,
            "citations": [],
            "adaptation_reason": "Memory reset."
        }
        st.rerun()

# ==========================================
# Main Header
# ==========================================
st.markdown("<div class='main-title'>EduPath — Personalized Tutoring Agent</div>", unsafe_allow_html=True)
st.markdown("""
<div style='margin-bottom: 12px;'>
    <span class='badge-pill badge-sdg'>🌐 UN SDG 4: Quality Education</span>
    <span class='badge-pill badge-google'>🏆 Google Solution Challenge</span>
    <span class='badge-pill badge-openstax'>📚 OpenStax Grounded</span>
    <span class='badge-pill badge-langgraph'>⚡ LangGraph Stateful Architecture</span>
</div>
<p style='color: #475569; font-size: 0.95rem; margin-bottom: 20px;'>
    Personalized 1-on-1 AI tutor designed for underserved schools. Adapts explanation style dynamically across 
    <b>3 difficulty levels</b> based on student mistakes and comprehension signals using few-shot in-context learning.
</p>
""", unsafe_allow_html=True)

# Tabs
tab_chat, tab_comparison, tab_arch = st.tabs([
    "💬 1-on-1 Interactive Tutoring",
    "📊 Multi-Level Comparison Matrix (Viva Deliverable)",
    "🧠 System Architecture & Methodology"
])

# ==========================================
# Tab 1: Interactive Chat
# ==========================================
with tab_chat:
    col_chat, col_quick = st.columns([3, 1])
    
    with col_quick:
        st.markdown("#### 💡 Quick Student Queries")
        st.caption("Click any classic high-school question or misconception to test adaptation:")
        
        sample_queries = {
            "physics": [
                "Why do heavier things fall faster than lighter things?",
                "If cart pulls back on horse with equal force, why does it move?",
                "I don't understand inertia, it feels too confusing."
            ],
            "maths": [
                "Why is 5 - (-3) = 8? Doesn't subtracting make it smaller?",
                "What is standard deviation and what does it tell us?",
                "If I flip a coin 5 times and get heads, is tails guaranteed next?"
            ],
            "biology": [
                "Do plants perform respiration or only photosynthesis?",
                "Why can't our cells survive without mitochondria?",
                "What is the difference between prokaryote and eukaryote cells?"
            ]
        }
        
        for q in sample_queries.get(st.session_state.subject, []):
            if st.button(q, key=f"btn_{q}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": q})
                
                # Execute LangGraph workflow
                with st.spinner("EduPath is reasoning and adapting..."):
                    state_input = {
                        "messages": st.session_state.messages,
                        "subject": st.session_state.subject,
                        "current_level": st.session_state.current_level,
                        "auto_adapt": st.session_state.auto_adapt,
                        "detected_misconceptions": st.session_state.detected_misconceptions,
                        "retrieved_context": "",
                        "citations": [],
                        "rag_score": 0.0,
                        "is_fallback": False,
                        "adaptation_reason": "",
                        "response": ""
                    }
                    result = tutor_graph_app.invoke(state_input)
                    
                    st.session_state.current_level = result["current_level"]
                    st.session_state.detected_misconceptions = result["detected_misconceptions"]
                    st.session_state.last_inspector = {
                        "rag_score": result["rag_score"],
                        "is_fallback": result["is_fallback"],
                        "citations": result.get("citations", []),
                        "adaptation_reason": result["adaptation_reason"]
                    }
                    st.session_state.messages.append({"role": "assistant", "content": result["response"]})
                st.rerun()

    with col_chat:
        # Display Conversation History
        chat_container = st.container()
        with chat_container:
            if not st.session_state.messages:
                st.info(f"👋 Welcome to EduPath **{st.session_state.subject.capitalize()}** Tutoring! Ask any question or try one of the classic questions on the right.")
                
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    with st.chat_message("user", avatar="🎒"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant", avatar="🎓"):
                        st.markdown(msg["content"])
                        
                        # Show citation footer if available
                        citations = st.session_state.last_inspector.get("citations", [])
                        if citations and msg == st.session_state.messages[-1]:
                            citation_badges = [f"📖 *OpenStax p.{c['page']} (Conf: {c['score']})*" for c in citations[:2]]
                            st.caption("Verified Grounding: " + " | ".join(citation_badges))

        # User Text Input
        user_input = st.chat_input(f"Ask EduPath a question in {st.session_state.subject.capitalize()}...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.spinner("EduPath is reasoning and adapting..."):
                state_input = {
                    "messages": st.session_state.messages,
                    "subject": st.session_state.subject,
                    "current_level": st.session_state.current_level,
                    "auto_adapt": st.session_state.auto_adapt,
                    "detected_misconceptions": st.session_state.detected_misconceptions,
                    "retrieved_context": "",
                    "citations": [],
                    "rag_score": 0.0,
                    "is_fallback": False,
                    "adaptation_reason": "",
                    "response": ""
                }
                result = tutor_graph_app.invoke(state_input)
                
                st.session_state.current_level = result["current_level"]
                st.session_state.detected_misconceptions = result["detected_misconceptions"]
                st.session_state.last_inspector = {
                    "rag_score": result["rag_score"],
                    "is_fallback": result["is_fallback"],
                    "citations": result.get("citations", []),
                    "adaptation_reason": result["adaptation_reason"]
                }
                st.session_state.messages.append({"role": "assistant", "content": result["response"]})
            st.rerun()

# ==========================================
# Tab 2: Multi-Level Comparison Matrix
# ==========================================
with tab_comparison:
    st.markdown("### 📊 Side-by-Side Multi-Level Adaptation Matrix")
    st.markdown("""
    **Primary Viva / Rubric Deliverable:** Demonstrates how EduPath dynamically adjusts its pedagogical strategy, vocabulary, 
    and cognitive scaffolding across **Level 1**, **Level 2**, and **Level 3** for the *exact same concept*.
    """)
    
    test_subject = st.selectbox(
        "Select Subject for Matrix Evaluation:",
        options=["physics", "maths", "biology"],
        key="matrix_subject"
    )
    
    default_prompt = {
        "physics": "When a horse pulls a cart, the cart pulls back on the horse with equal force. Why does the cart move at all?",
        "maths": "What is the difference between Mean, Median, and Mode, and when should we use which?",
        "biology": "Why do humans need oxygen, and how is cellular respiration connected to the food we eat?"
    }[test_subject]
    
    matrix_query = st.text_area("Enter STEM Concept / Student Question:", value=default_prompt, height=70)
    
    if st.button("🚀 Generate Multi-Level Comparison Matrix", type="primary"):
        with st.spinner("Generating Level 1, Level 2, and Level 3 explanations..."):
            comparison_results = generate_multilevel_comparison(matrix_query, subject=test_subject)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🟢 Level 1: Foundational")
                st.caption("**Target:** Underserved / Struggling Student")
                st.markdown("<span class='level-badge-1'>Intuitive Analogies & Zero Jargon</span>", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown(comparison_results[1]["response"])
                if comparison_results[1]["citations"]:
                    st.caption(f"Grounding: OpenStax p.{comparison_results[1]['citations'][0]['page']}")

            with col2:
                st.markdown("#### 🔵 Level 2: Conceptual")
                st.caption("**Target:** Standard Grade 9/10 Student")
                st.markdown("<span class='level-badge-2'>Structured Steps & Standard Formulas</span>", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown(comparison_results[2]["response"])
                if comparison_results[2]["citations"]:
                    st.caption(f"Grounding: OpenStax p.{comparison_results[2]['citations'][0]['page']}")

            with col3:
                st.markdown("#### 🟣 Level 3: Socratic")
                st.caption("**Target:** Advanced / AP-Prep Student")
                st.markdown("<span class='level-badge-3'>Probing Inquiries & Boundary Scenarios</span>", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown(comparison_results[3]["response"])
                if comparison_results[3]["citations"]:
                    st.caption(f"Grounding: OpenStax p.{comparison_results[3]['citations'][0]['page']}")

# ==========================================
# Tab 3: Architecture & SDG 4 Alignment
# ==========================================
with tab_arch:
    st.markdown("### 🧠 AI System Architecture & SDG 4 Impact")
    
    col_sdg, col_pipeline = st.columns([1, 1])
    
    with col_sdg:
        st.markdown("#### 🌐 UN SDG 4: Quality Education Alignment")
        st.markdown("""
        - **Problem Addressed:** In underserved and under-resourced schools, the student-to-teacher ratio is often 40:1 or worse. Teachers lack the time to diagnose individual student misconceptions or cater to varying learning paces.
        - **EduPath Solution:** Acts as an equitable, always-available 1-on-1 pedagogical companion that:
          1. **Democratizes Quality Pedagogy:** Grounds learning in open-license, peer-reviewed OpenStax curriculum.
          2. **Eliminates STEM Anxiety:** Adapts explanation styles to Level 1 analogies for struggling students so they never feel abandoned.
          3. **Promotes Critical Mastery:** Challenges proficient students with Socratic inquiry (Level 3) rather than repetitive drill exercises.
        """)
        
    with col_pipeline:
        st.markdown("#### ⚙️ Technical AI Innovations")
        st.markdown("""
        - **LangGraph Stateful Machine:** Maintains a sliding conversational memory window and multi-turn student error states (`detected_misconceptions`).
        - **Dense Vector Embeddings (SentenceTransformers):** Uses `all-MiniLM-L6-v2` to map 1,690+ textbook chunks to a 384-dimensional dense semantic vector space.
        - **Two-Stage RAG with Similarity Thresholding:** Computes normalized cosine similarity over dense vectors.
        - **Autonomous Graceful Fallback:** If query semantic confidence falls below threshold ($< 0.32$), the system transparently shifts to Groq's general AI model without crashing.
        - **Few-Shot In-Context Pedagogy:** Calibrates tone, cognitive load, and problem-solving scaffolding on-the-fly without needing expensive parameter fine-tuning.
        """)
        
    st.markdown("---")
    st.markdown("#### 📊 OpenStax Dense Corpus Statistics")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Physics Chunks Indexed", "587 chunks (384-dim)", "OpenStax High School Physics")
    col_b.metric("Maths/Stats Chunks Indexed", "508 chunks (384-dim)", "OpenStax High School Statistics")
    col_c.metric("Biology Chunks Indexed", "599 chunks (384-dim)", "OpenStax Concepts of Biology")
