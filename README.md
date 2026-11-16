# 🎓 EduPath — Personalized Tutoring Agent
> **Google Solution Challenge — UN SDG 4: Quality Education**  
> **Course:** CSE 473 (Artificial Intelligence)

---

## 📌 Project Overview
In underserved and resource-constrained schools, high student-to-teacher ratios (often 40:1 or worse) prevent educators from diagnosing individual student misconceptions or pacing instruction. 

**EduPath** is a stateful AI tutoring agent built with **LangGraph**, **Groq LLM (`openai/gpt-oss-120b`)**, and **official NCERT Class 11 & 12 Textbooks**. It dynamically diagnoses student misunderstandings and adapts its pedagogical explanation style across **3 difficulty levels** using **few-shot in-context learning**.

---

## 🚀 Key Features & AI Innovations

### 1. ChatGPT-Style Dynamic Level Switcher (The Innovation)
- **Zero-Cramping Single Stream**: Answers appear in a clean, full-width Notion/Linear style chat canvas.
- **Instant Level Pills**: Every assistant message features `[🌱 Foundational]`, `[📘 Conceptual]`, and `[🧠 Socratic]` toggle pills.
- **Zero-Latency Switching**: Clicking any pill switches the explanation instantly between levels without re-generating or page refreshing.
- **Preference Memory**: When a student chooses Level 2, future answers automatically adapt to Level 2 as the preferred default.
- **Crisp LaTeX Math Rendering**: Built with `rehype-katex` so formulas ($\frac{\Delta v}{\Delta t}, F=ma$) render in beautiful, textbook-quality math typography.

### 2. Multi-Level Pedagogical Adaptation (Core Deliverable)
- **Level 1 (Foundational / Intuitive):** For struggling or underserved students. Employs vivid everyday physical analogies (e.g., skateboards, ice rinks, debt/allowance) and eliminates intimidating mathematical jargon.
- **Level 2 (Conceptual & Guided):** Standard Class 11/12 NCERT curriculum level. Structured textbook explanations, standard formulas, and step-by-step problem-solving.
- **Level 3 (Socratic & Critical Inquiry):** For advanced / competitive exam prep (JEE/NEET). Uses Socratic questioning, boundary-condition tests ("what happens if friction is zero?"), and thought experiments without spoon-feeding answers.

### 3. NCERT Textbook Grounding & Dense Neural RAG
- Indexed over **1,740+ semantic chunks** from official NCERT Class 11 & 12 textbooks using `RecursiveCharacterTextSplitter`:
  - ⚛️ *NCERT Physics (Classes XI & XII)* (692 chunks)
  - 🧪 *NCERT Chemistry (Classes XI & XII)* (684 chunks)
  - 📐 *NCERT Mathematics (Classes XI & XII)* (364 chunks)
- **SentenceTransformers (`all-MiniLM-L6-v2`)**: Maps text chunks into a **384-dimensional dense semantic vector space**.
- Normalized Cosine Distance with verified page citations.

### 4. Similarity Thresholding & Graceful Fallback
- If cosine similarity $\ge 0.32$: Responses are strictly grounded in NCERT with page citations.
- If similarity $< 0.32$ (out-of-syllabus query): Transparently activates **Autonomous Fallback Mode** via Groq AI without crashing.

### 5. LangGraph Stateful Agent with Memory Window
- Maintains a conversational sliding memory window.
- Persists cumulative student errors in `detected_misconceptions` to continually refine explanations across multi-turn interactions.

---

## 📁 Repository Structure
```
llm_project/
├── dataset/
│   ├── physics/       # OpenStax High School Physics PDF
│   ├── maths/         # OpenStax High School Statistics PDF
│   └── biology/       # OpenStax Concepts of Biology PDF
├── .env               # Groq API Key
├── ingest.py          # PDF text extraction & vector indexing script
├── openstax_index.pkl # Persistent pre-computed vector index
├── tutor_agent.py     # LangGraph state machine, few-shot prompts & RAG
├── app.py             # Streamlit interactive web application
└── README.md          # Documentation and viva preparation guide
```

---

## 🏃 How to Run Locally

### 1. Activate Conda Environment:
```powershell
conda activate langgraph_env
```

### 2. (Optional) Rebuild OpenStax Index:
```powershell
python ingest.py
```

### 3. Launch Streamlit Web Application:
```powershell
streamlit run app.py
```
Open your browser at: **`http://localhost:8501`**

---

## 🎓 Viva / Presentation Guide (Key AI Questions)

| Question Examiner Might Ask | Technical Answer to Give |
| :--- | :--- |
| **Why not just use standard ChatGPT?** | Standard LLMs are one-size-fits-all and hallucinate. EduPath uses **few-shot pedagogical exemplars** to enforce 3 calibrated levels, grounds facts in **OpenStax peer-reviewed curriculum**, and tracks misconceptions over multi-turn dialogues via **LangGraph**. |
| **Why did you use LangGraph?** | LangGraph provides an explicit state machine (`TutorState`) with sequential nodes (`Assess` ➔ `Retrieve` ➔ `Generate`). It maintains multi-turn memory and tracks student misconception states across turns. |
| **How does Fallback work?** | We enforce a similarity threshold ($0.15$). If an inquiry has a low cosine score, EduPath flags `is_fallback = True`, generating transparent general AI answers while noting the source. |
| **Which OpenStax books did you choose?** | Because SDG 4 specifically targets *underserved schools*, university-level calculus or tensor physics would be inappropriate. We specifically grounded our agent in **OpenStax High School Physics, High School Statistics, and Concepts of Biology**. |
