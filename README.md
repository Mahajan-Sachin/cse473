# 🎓 EduPath — Personalized AI Tutoring Agent
> **Google Solution Challenge — UN SDG 4: Quality Education**  
> **Course:** CSE 473 (Artificial Intelligence)  
> **Knowledge Base:** Official NCERT STEM Curriculum (Classes 11 & 12: Physics, Chemistry, Mathematics)

---

## 📌 Project Overview
In resource-constrained and underserved educational systems, high student-to-teacher ratios (frequently exceeding 40:1) make it nearly impossible for instructors to detect individual conceptual misunderstandings, track learning plateaus, or adapt teaching style to each student's pace.

**EduPath** is an adaptive, stateful AI tutoring agent built with **LangGraph**, **Groq LLM (`openai/gpt-oss-120b`)**, and **persistent ChromaDB vector indexing**. Grounded in official **NCERT Class 11 & 12 STEM textbooks**, EduPath dynamically diagnoses student misconceptions, tracks them across conversational state, and generates answers calibrated across **3 pedagogical cognitive levels** using **few-shot in-context learning**.

---

## 🚀 Key Features & AI Innovations

### 1. ChatGPT-Style Dynamic Level Toggle (Interactive UI)
- **Zero-Cramping Canvas:** Single-stream conversational interface designed with a clean, distraction-free aesthetic (inspired by Notion & Linear).
- **Instant Level Pills on Every Message:** Every tutor response features intuitive toggle pills:
  - `[🌱 Foundational]`
  - `[📘 Conceptual]`
  - `[🧠 Socratic]`
- **Zero-Latency Instant Switching:** The FastAPI backend concurrently generates all 3 levels using a thread pool. Students can toggle between explanation depths instantly with zero waiting or regeneration.
- **Preference Memory:** Choosing a preferred level updates the conversational state, automatically setting that level as the default for follow-up questions.
- **Crisp KaTeX Math Rendering:** Built with `rehype-katex` and `remark-math` so complex equations ($\vec{F} = m\vec{a}$, $\Delta H = \Delta U + P\Delta V$, $\sigma = \sqrt{\frac{\sum (x-\mu)^2}{N}}$) render in sharp, textbook-grade typography.

### 2. Multi-Level Pedagogical Adaptation (Core Deliverable)
- **🌱 Level 1 (Foundational & Intuitive):** Built for students struggling with basic concepts. Replaces intimidating mathematical jargon with vivid physical analogies (skateboards, ice rinks, debt/allowance, water pipes) to build visceral intuition.
- **📘 Level 2 (Conceptual & Guided):** Standard Class 11/12 NCERT textbook depth. Structured step-by-step reasoning, formal SI units, canonical formulas, and worked examples.
- **🧠 Level 3 (Socratic & Critical Inquiry):** For competitive exam preparation (JEE/NEET). Refuses to spoon-feed answers; challenges the student with counterfactual boundary scenarios (*"What happens to acceleration if friction goes to zero?"*) and guided questioning.

### 3. NCERT Textbook Grounding & Neural Semantic RAG
- Indexed over **1,740+ boundary-aware semantic chunks** from official NCERT Class 11 & 12 textbooks:
  - ⚛️ **NCERT Physics (Classes XI & XII):** Kinematics, Laws of Motion, Work/Energy/Power, Gravitation, Waves & Thermodynamics (692 chunks).
  - 🧪 **NCERT Chemistry (Classes XI & XII):** Atomic Structure, Chemical Bonding, Thermodynamics, Equilibrium, Organic Chemistry (684 chunks).
  - 📐 **NCERT Mathematics (Classes XI & XII):** Sets, Relations, Calculus, Coordinate Geometry, Probability & Statistics (364 chunks).
- **Semantic Text Splitter:** Uses LangChain's `RecursiveCharacterTextSplitter` with hierarchical separators `["\n\n", "\n", ". ", " ", ""]` to ensure chunks never split across mid-sentence or mid-equation boundaries.
- **Dense Vector Embeddings:** Encoded via `sentence-transformers/all-MiniLM-L6-v2` into a 384-dimensional dense semantic space stored in a persistent **ChromaDB** vector store with HNSW Cosine Distance indexing.

### 4. Dynamic Misconception Tracking & Remediation
- An LLM assessment sub-routine analyzes every student prompt for ingrained conceptual errors (e.g., *"heavier objects fall faster in a vacuum"*, *"gravity is an acceleration, not a force"*).
- Misconceptions are persisted in the agent's `detected_misconceptions` state list and fed into subsequent generation nodes so the tutor proactively dismantles them.

### 5. Similarity Thresholding & Graceful Fallback
- **Threshold ($\ge 0.32$):** Query is grounded directly in verified NCERT textbook chunks with page citations.
- **Out-of-Syllabus ($\mathbf{< 0.32}$):** Activates **Autonomous Fallback Mode** via Groq AI without crashing, answering gracefully while maintaining scientific fidelity.

---

## 🏗️ System Architecture

```
                                  ┌───────────────────────────┐
                                  │   React 19 + Vite UI     │
                                  │ (KaTeX, Tailwind, Pills)  │
                                  └─────────────┬─────────────┘
                                                │ REST API (JSON)
                                                ▼
                                  ┌───────────────────────────┐
                                  │   FastAPI Backend Server  │
                                  │        (Port 8000)        │
                                  └─────────────┬─────────────┘
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
     ┌───────────────────────┐                                     ┌───────────────────────┐
     │  LangGraph Engine     │                                     │  ChromaDB Vector DB   │
     │  Stateful Graph:      │                                     │  - 1,740 NCERT Chunks │
     │  1. Assess Misconcept │ ──── Queries Cosine Distance ─────▶ │  - 384-dim Embeddings │
     │  2. Retrieve Context  │                                     │  - HNSW Indexing      │
     │  3. Adaptive Generate │ ◀─── Top-K Grounded Chunks ─────────│  - Page Citations     │
     └───────────┬───────────┘                                     └───────────────────────┘
                 │
                 ▼
     ┌───────────────────────┐
     │   Groq LLM Engine     │
     │ (openai/gpt-oss-120b) │ ──── Generates Levels 1, 2, 3 Concurrently ───▶ React Canvas
     └───────────────────────┘
```

---

## 📁 Repository Structure

```
llm_project/
├── dataset/
│   ├── physics/        # NCERT Physics Complete PDF (Classes 11 & 12)
│   ├── chemistry/      # NCERT Chemistry Complete PDF (Classes 11 & 12)
│   └── maths/          # NCERT Mathematics Complete PDF (Classes 11 & 12)
├── frontend/           # Modern React 19 Frontend
│   ├── src/
│   │   ├── App.jsx     # Main UI with Level Toggle Pills & LaTeX Rendering
│   │   ├── App.css     # Notion/Linear minimal styling
│   │   └── main.jsx    # Vite React entry point
│   ├── package.json    # React, Lucide, KaTeX, Tailwind dependencies
│   └── vite.config.js  # Vite dev server & proxy configuration
├── chroma_db/          # Persistent ChromaDB vector database
├── tutor_agent.py      # LangGraph state machine, few-shot prompts, & RAG node
├── server.py           # FastAPI REST API with concurrent 3-level generation
├── ingest.py           # PyMuPDF extraction & RecursiveCharacterTextSplitter
├── run.bat             # One-click runner for both Backend & Frontend
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── README.md           # Documentation & Viva Defence Guide
```

---

## 🏃 How to Run Locally

### Prerequisites
- Python 3.10 or 3.11 with Conda
- Node.js (v18+)
- A free Groq API key from [console.groq.com](https://console.groq.com)

### 1. Environment Setup
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

Install Python dependencies:
```powershell
conda activate langgraph_env
pip install -r requirements.txt
```

Install Frontend dependencies:
```powershell
cd frontend
npm install
cd ..
```

---

### 2. (Optional) Rebuild the NCERT Vector Database
To re-index the textbooks from scratch:
```powershell
python ingest.py
```

---

### 3. Launch the Application (One-Click)

Simply double-click **`run.bat`** (or execute from terminal):
```powershell
.\run.bat
```
This concurrently starts:
* **FastAPI Backend:** `http://127.0.0.1:8000`
* **Vite React UI:** `http://localhost:5173`

Open your browser at **`http://localhost:5173`**.

---

## 🎓 Viva & Presentation Defense Guide (Key Technical Questions)

| Question Examiner Might Ask | Technical Answer to Give |
| :--- | :--- |
| **Why not just use standard ChatGPT?** | General LLMs are one-size-fits-all and hallucinate outside their training distribution. EduPath uses **few-shot pedagogical exemplars** to enforce 3 calibrated cognitive tiers, grounds factual statements directly in official **NCERT curriculum**, and tracks student misconceptions across turns via **LangGraph**. |
| **Why did you switch to NCERT over OpenStax?** | For Indian education and university evaluation, NCERT is the national gold standard across CBSE, State Boards, JEE, and NEET. Grounding in NCERT ensures SI unit consistency, standard Indian textbook definitions, and relatable citations for Indian students and evaluators. |
| **Why LangGraph over basic LangChain chains?** | LangChain chains are unidirectional DAGs. LangGraph provides an explicit cyclic state machine (`TutorState`) with sequential nodes (`Assess` ➔ `Retrieve` ➔ `Generate`), enabling persistent misconception tracking and dynamic adaptation based on conversational memory. |
| **Why RecursiveCharacterTextSplitter?** | Naive character splitting cuts words or formulas in half. `RecursiveCharacterTextSplitter` respects natural grammatical boundaries hierarchically (paragraphs `\n\n` $\to$ lines `\n` $\to$ sentences `. ` $\to$ words), preserving complete semantic thoughts for dense neural encoding. |
| **How does misconception remediation work?** | In the `Assess` node, a fast LLM pass scans the student's question against common pedagogical misconceptions. If detected, the fallacy is logged to `detected_misconceptions` and injected into the prompt so the tutor directly unteaches the error. |
| **Why FastAPI + React instead of Streamlit?** | Streamlit re-runs the entire Python script on every user interaction, causing screen flashes, cold starts, and poor layout control. Our decoupled architecture pairs a high-performance **FastAPI backend** (concurrent 3-level generation) with a modern **React 19 single-page canvas** featuring instant zero-latency pill switching and native KaTeX rendering. |
| **How does Fallback Mode prevent hallucination?** | We enforce a cosine similarity threshold of $0.32$. If a query falls outside the indexed NCERT syllabus, the system transparently flags `is_fallback = True` and signals this to the student, ensuring no ungrounded claims are disguised as textbook facts. |

---

## 📜 Course & Competition Credentials
* **Project:** EduPath — Personalized Tutoring Agent
* **Course:** CSE 473 — Artificial Intelligence
* **Theme:** Google Solution Challenge | UN Sustainable Development Goal 4 (Quality Education)
