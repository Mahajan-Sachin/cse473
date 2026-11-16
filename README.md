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

## 🔬 Engineering & Design Methodology

### 1. Pedagogical Calibration via Few-Shot In-Context Learning
Unlike generic conversational LLMs that produce one-size-fits-all answers, EduPath enforces strict pedagogical calibration across three distinct cognitive tiers (`Foundational`, `Conceptual`, and `Socratic`). Few-shot exemplars dynamically dictate explanation depth, vocabulary, and questioning style to cater to varied learner proficiencies.

### 2. State-Driven Misconception Diagnosis
Using LangGraph's state machine architecture (`TutorState`), EduPath models a sequential loop (`Assess` ➔ `Retrieve` ➔ `Generate`). During the assessment phase, student queries are diagnosed for underlying conceptual fallacies, which are persisted into a session-level state list (`detected_misconceptions`) to guide subsequent remediation.

### 3. Curriculum-Aligned Neural RAG
The knowledge base is strictly aligned with the official NCERT STEM curriculum (Classes 11 & 12). Raw textbook streams are partitioned using LangChain's `RecursiveCharacterTextSplitter` across natural grammatical boundaries (`\n\n`, `\n`, `. `, ` `) to prevent formula truncation. Chunks are encoded into 384-dimensional dense vectors via `sentence-transformers/all-MiniLM-L6-v2` and indexed within a persistent ChromaDB vector store using HNSW Cosine Distance.

### 4. Hallucination Safeguards & Confidence Thresholding
To ensure high factual fidelity, a cosine similarity threshold ($\tau = 0.32$) gates retrieval. Out-of-syllabus inquiries trigger a transparent **Autonomous Fallback Mode**, ensuring that unsupported claims are never falsely attributed to textbook citations.

### 5. Decoupled Full-Stack Architecture
EduPath separates a high-throughput **FastAPI backend** from an interactive **React 19 single-page canvas**. The backend leverages concurrent thread pooling to synthesize all three pedagogical levels simultaneously, enabling zero-latency level toggling with hardware-accelerated KaTeX mathematical rendering.

---

## 📜 Project Metadata
* **Project Name:** EduPath — Personalized AI Tutoring Agent
* **Course:** CSE 473 — Artificial Intelligence
* **Initiative:** UN Sustainable Development Goal 4 (Quality Education) | Google Solution Challenge
