import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { 
  Sparkles, 
  Send, 
  BookOpen, 
  Layers, 
  AlertTriangle, 
  RefreshCw, 
  CheckCircle2, 
  Atom, 
  Sigma, 
  FlaskConical,
  Dna, 
  Info, 
  ChevronRight, 
  GraduationCap,
  Sliders,
  ExternalLink,
  HelpCircle,
  X
} from 'lucide-react';

const SUBJECT_CONFIG = {
  physics: {
    name: "NCERT Physics (Class 11 & 12)",
    book: "NCERT Physics (Classes XI & XII)",
    icon: Atom,
    color: "blue",
    sampleQuestions: [
      "Why do heavier things fall at the same speed as light things in a vacuum?",
      "If a cart pulls back on a horse with equal force, why does the cart move at all?",
      "What is the difference between acceleration and gravity according to NCERT?"
    ]
  },
  chemistry: {
    name: "NCERT Chemistry (Class 11 & 12)",
    book: "NCERT Chemistry (Classes XI & XII)",
    icon: FlaskConical,
    color: "purple",
    sampleQuestions: [
      "Why does ice float on water? Explain via hydrogen bonding.",
      "What is the difference between molarity and molality, and which is temperature independent?",
      "Explain Le Chatelier's principle with an intuitive analogy."
    ]
  },
  maths: {
    name: "NCERT Mathematics (Class 11 & 12)",
    book: "NCERT Mathematics (Classes XI & XII)",
    icon: Sigma,
    color: "emerald",
    sampleQuestions: [
      "What is standard deviation and how does it measure dispersion?",
      "Can the probability of an event ever be greater than 1 or negative?",
      "Why is dividing by zero undefined in mathematics?"
    ]
  }
};

const LEVEL_CONFIG = {
  1: {
    label: "Level 1: Foundational",
    shortLabel: "Foundational",
    tagline: "Everyday Analogies & Zero Jargon",
    icon: "🌱",
    pillClass: "bg-emerald-50 text-emerald-800 border-emerald-300 hover:bg-emerald-100",
    activeClass: "bg-emerald-600 text-white border-emerald-600 shadow-sm"
  },
  2: {
    label: "Level 2: Conceptual",
    shortLabel: "Conceptual",
    tagline: "Structured Steps & Textbook Formulas",
    icon: "📘",
    pillClass: "bg-sky-50 text-sky-800 border-sky-300 hover:bg-sky-100",
    activeClass: "bg-sky-600 text-white border-sky-600 shadow-sm"
  },
  3: {
    label: "Level 3: Socratic",
    shortLabel: "Socratic",
    tagline: "Critical Inquiry & Boundary Scenarios",
    icon: "🧠",
    pillClass: "bg-purple-50 text-purple-800 border-purple-300 hover:bg-purple-100",
    activeClass: "bg-purple-600 text-white border-purple-600 shadow-sm"
  }
};

const preprocessMarkdown = (content) => {
  if (!content) return "";
  let text = content;
  // Convert [ a = \frac{...} ] or [ F_g = mg ] math in brackets to $...$
  text = text.replace(/\[\s*([a-zA-Z_]\s*=\s*[\s\S]*?)\s*\]/g, (match, formula) => {
    if (formula.includes('\\') || formula.includes('^') || formula.includes('_')) {
      return `$${formula.trim()}$`;
    }
    return match;
  });
  // Convert \[ ... \] to $$ ... $$
  text = text.replace(/\\\[([\s\S]*?)\\\]/g, (_, math) => `\n\n$$\n${math.trim()}\n$$\n\n`);
  // Convert \( ... \) to $ ... $
  text = text.replace(/\\\(([\s\S]*?)\\\)/g, (_, math) => `$${math.trim()}$`);
  // Fix inline concatenated tables: replace "||" with newline and "|"
  text = text.replace(/\|\|\s*/g, '|\n| ');
  // Remove any blank lines between table rows so markdown tables are strictly continuous
  text = text.replace(/(\|[^\r\n]+\|)\s*\r?\n(?:\s*\r?\n)+\s*(\|)/g, '$1\n$2');
  // Ensure a blank line exists BEFORE the table begins (only if previous line was NOT a table row)
  text = text.replace(/([^\r\n|])\r?\n\s*(\|)/g, '$1\n\n$2');
  // Ensure a blank line exists AFTER the table ends (only if next line is NOT a table row)
  text = text.replace(/(\|[^\r\n]*)\r?\n([^\r\n|])/g, '$1\n\n$2');
  return text;
};

export default function App() {
  const [subject, setSubject] = useState("physics");
  const [currentLevel, setCurrentLevel] = useState(1);
  const [autoAdapt, setAutoAdapt] = useState(true);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [misconceptions, setMisconceptions] = useState([]);
  const [showArchModal, setShowArchModal] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    setInput("");
    const userMessage = { role: "user", content: query };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: query,
          subject: subject,
          current_level: currentLevel,
          auto_adapt: autoAdapt,
          history: messages.map(m => {
            const text = m.role === "assistant" 
              ? (m.levels?.[m.activeLevel]?.text || m.content || "")
              : (m.content || "");
            return { role: m.role, content: text };
          }).filter(m => m.content && m.content.trim().length > 0),
          detected_misconceptions: misconceptions
        })
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      
      // Determine chosen active level for this new answer
      const chosenLevel = data.primary_level || currentLevel;
      if (autoAdapt && chosenLevel !== currentLevel) {
        setCurrentLevel(chosenLevel);
      }

      setMisconceptions(data.detected_misconceptions || []);

      const assistantMessage = {
        role: "assistant",
        content: data.levels?.[chosenLevel]?.text || "",
        activeLevel: chosenLevel,
        levels: data.levels,
        citations: data.citations || [],
        rag_score: data.rag_score,
        is_fallback: data.is_fallback,
        adaptation_reason: data.adaptation_reason,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages([...newMessages, assistantMessage]);
    } catch (err) {
      console.error("Chat error:", err);
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          activeLevel: currentLevel,
          levels: {
            [currentLevel]: {
              text: `⚠️ **Error connecting to EduPath API**: ${err.message}. Please verify the backend server is running on port 8000.`,
              citations: [],
              rag_score: 0.0,
              is_fallback: true
            }
          },
          citations: [],
          rag_score: 0.0,
          is_fallback: true,
          adaptation_reason: "Connection failure fallback"
        }
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSwitchMessageLevel = (messageIndex, newLvl) => {
    setMessages(prev => {
      const updated = [...prev];
      if (updated[messageIndex]) {
        updated[messageIndex] = {
          ...updated[messageIndex],
          activeLevel: newLvl
        };
      }
      return updated;
    });

    // Update global preferred level so subsequent questions follow this choice
    setCurrentLevel(newLvl);
  };

  const handleReset = () => {
    setMessages([]);
    setMisconceptions([]);
    setCurrentLevel(1);
  };

  const currentSubjectMeta = SUBJECT_CONFIG[subject] || SUBJECT_CONFIG.physics;
  const SubjectIcon = currentSubjectMeta.icon;

  return (
    <div className="flex h-screen bg-[#F8FAFC] text-slate-900 overflow-hidden font-sans">
      
      {/* ========================================================= */}
      {/* 1. LEFT SIDEBAR (Notion / Linear Minimalist Panel)       */}
      {/* ========================================================= */}
      <aside className={`
        ${sidebarOpen ? 'w-80' : 'w-0 -translate-x-full'} 
        transition-all duration-300 ease-in-out border-r border-slate-200 bg-white flex flex-col z-20 shrink-0
      `}>
        {/* Workspace Brand */}
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold shadow-sm">
              <GraduationCap size={18} />
            </div>
            <div>
              <div className="font-semibold text-sm tracking-tight flex items-center gap-1.5">
                EduPath Tutor
                <span className="text-[10px] font-medium bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded border border-blue-200">
                  SDG 4
                </span>
              </div>
              <div className="text-[11px] text-slate-500">Google Solution Challenge</div>
            </div>
          </div>
        </div>

        {/* Scrollable Configuration */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          
          {/* Target Subject Selector */}
          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-600 block mb-2">
              STEM Domain / Book
            </label>
            <div className="space-y-1.5">
              {Object.entries(SUBJECT_CONFIG).map(([key, cfg]) => {
                const Icon = cfg.icon;
                const active = subject === key;
                return (
                  <button
                    key={key}
                    onClick={() => {
                      setSubject(key);
                      handleReset();
                    }}
                    className={`
                      w-full text-left px-3 py-2.5 rounded-lg text-xs font-medium flex items-center justify-between transition-all
                      ${active 
                        ? 'bg-slate-900 text-white shadow-sm' 
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 border border-transparent'
                      }
                    `}
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <Icon size={15} className={active ? 'text-blue-300' : 'text-slate-600'} />
                      <span className="truncate">{cfg.name}</span>
                    </div>
                    {active && <CheckCircle2 size={13} className="text-blue-400 shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Level Strategy */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-600">
                Cognitive Level
              </label>
              <button 
                onClick={() => setAutoAdapt(!autoAdapt)}
                className={`text-[10px] font-medium px-2 py-0.5 rounded transition ${
                  autoAdapt 
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                    : 'bg-slate-100 text-slate-600'
                }`}
              >
                {autoAdapt ? "⚡ Auto-Adapt" : "🎚️ Manual Lock"}
              </button>
            </div>

            <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 space-y-2">
              {Object.entries(LEVEL_CONFIG).map(([lvlStr, cfg]) => {
                const lvl = parseInt(lvlStr);
                const isSelected = currentLevel === lvl;
                return (
                  <button
                    key={lvl}
                    onClick={() => setCurrentLevel(lvl)}
                    className={`
                      w-full text-left p-2 rounded-md text-xs transition-all flex items-start gap-2 border
                      ${isSelected 
                        ? 'bg-white border-slate-300 shadow-xs' 
                        : 'border-transparent text-slate-500 hover:bg-slate-100/70 hover:text-slate-800'
                      }
                    `}
                  >
                    <span className="text-sm">{cfg.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className={`font-semibold ${isSelected ? 'text-slate-900' : 'text-slate-600'}`}>
                        {cfg.label}
                      </div>
                      <div className="text-[10px] text-slate-600 truncate">{cfg.tagline}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tracked Misconceptions / Diagnoses */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                <AlertTriangle size={12} className="text-amber-500" />
                Diagnosed Misconceptions
              </label>
              <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-500 font-mono">
                {misconceptions.length}
              </span>
            </div>
            
            {misconceptions.length > 0 ? (
              <div className="space-y-1.5">
                {misconceptions.slice(-3).map((misc, idx) => (
                  <div key={idx} className="text-[11px] bg-amber-50/70 border border-amber-200 text-amber-900 p-2 rounded-md leading-relaxed">
                    ⚠️ {misc}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-[11px] text-slate-500 italic bg-slate-50 p-2.5 rounded border border-slate-200/60">
                No conceptual fallacies detected yet.
              </div>
            )}
          </div>

          {/* OpenStax RAG Status */}
          <div className="bg-blue-50/50 border border-blue-200/80 rounded-lg p-3 text-xs space-y-1.5">
            <div className="font-semibold text-blue-900 flex items-center gap-1.5">
              <BookOpen size={13} className="text-blue-600" />
              Verified Knowledge Base
            </div>
            <div className="text-[11px] text-slate-600 leading-normal">
              Grounded in <span className="font-medium text-slate-800">{currentSubjectMeta.book}</span> with persistent ChromaDB dense vector indexing.
            </div>
          </div>

        </div>

        {/* Sidebar Footer */}
        <div className="p-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <button 
            onClick={handleReset}
            className="flex items-center gap-1.5 text-slate-500 hover:text-slate-800 py-1 px-2 rounded hover:bg-slate-100 transition"
          >
            <RefreshCw size={13} />
            Reset Session
          </button>
          <button 
            onClick={() => setShowArchModal(true)}
            className="flex items-center gap-1 text-blue-600 hover:text-blue-700 py-1 px-2 rounded hover:bg-blue-50 font-medium transition"
          >
            <Info size={13} />
            Architecture
          </button>
        </div>
      </aside>

      {/* ========================================================= */}
      {/* 2. MAIN CHAT ARENA (Full Width, Crisp Canvas)             */}
      {/* ========================================================= */}
      <main className="flex-1 flex flex-col min-w-0 h-full relative bg-[#F8FAFC]">
        
        {/* Top Navbar */}
        <header className="h-14 border-b border-slate-200 bg-white/90 backdrop-blur-xs px-6 flex items-center justify-between shrink-0 z-10">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 rounded-md hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition"
              title="Toggle sidebar"
            >
              <Sliders size={16} />
            </button>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm text-slate-900">{currentSubjectMeta.name}</span>
              <span className="text-slate-300">/</span>
              <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                Active Preference: 
                <span className="font-semibold text-slate-800">{LEVEL_CONFIG[currentLevel]?.label}</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
              ChromaDB 384-dim HNSW
            </span>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              Llama-3 / GPT-OSS 120B
            </span>
          </div>
        </header>

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6">
          
          {/* Welcome Screen when Empty */}
          {messages.length === 0 && (
            <div className="max-w-2xl mx-auto my-12 text-center space-y-6">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center mx-auto shadow-md">
                <Sparkles size={24} />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
                  EduPath: Adaptive STEM Tutoring
                </h2>
                <p className="text-sm text-slate-500 max-w-lg mx-auto leading-relaxed">
                  1-on-1 personalized tutor designed for underserved schools. Ask any concept or test a classic misconception below to observe dynamic few-shot level adaptation.
                </p>
              </div>

              {/* Sample Questions Grid */}
              <div className="text-left pt-2">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-600 mb-3 text-center">
                  Try asking one of these classic {currentSubjectMeta.name} concepts:
                </div>
                <div className="space-y-2">
                  {currentSubjectMeta.sampleQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(q)}
                      className="w-full p-3 rounded-xl bg-white border border-slate-200 hover:border-blue-400 hover:shadow-xs transition text-left text-xs font-medium text-slate-700 flex items-center justify-between group"
                    >
                      <span className="group-hover:text-blue-600 transition">{q}</span>
                      <ChevronRight size={14} className="text-slate-300 group-hover:text-blue-500 group-hover:translate-x-0.5 transition" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Conversation Bubbles */}
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg, idx) => {
              const isUser = msg.role === "user";

              if (isUser) {
                return (
                  <div key={idx} className="flex justify-end">
                    <div className="bg-slate-900 text-white px-4 py-3 rounded-2xl rounded-tr-xs max-w-xl text-sm leading-relaxed shadow-xs">
                      {msg.content}
                    </div>
                  </div>
                );
              }

              // Assistant Message with ChatGPT-Style Level Switcher
              const activeLvl = msg.activeLevel || currentLevel;
              const levelData = msg.levels?.[activeLvl] || { text: msg.content || "Generating..." };

              return (
                <div key={idx} className="space-y-2">
                  
                  {/* Tutor Card Container */}
                  <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
                    
                    {/* Level Switcher Header Pill Bar */}
                    <div className="bg-slate-50/70 border-b border-slate-100 px-4 py-2.5 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mr-1">
                          Pedagogical Level:
                        </span>
                        
                        {/* 3 Level Pills */}
                        {[1, 2, 3].map((lvl) => {
                          const cfg = LEVEL_CONFIG[lvl];
                          const isSelected = activeLvl === lvl;
                          return (
                            <button
                              key={lvl}
                              onClick={() => handleSwitchMessageLevel(idx, lvl)}
                              className={`
                                text-xs font-semibold px-2.5 py-1 rounded-md border transition-all flex items-center gap-1.5
                                ${isSelected ? cfg.activeClass : cfg.pillClass}
                              `}
                              title={cfg.tagline}
                            >
                              <span>{cfg.icon}</span>
                              <span>{cfg.shortLabel}</span>
                            </button>
                          );
                        })}
                      </div>

                      {/* Fallback or Grounding Indicator */}
                      <div className="text-[11px] text-slate-500 font-mono">
                        {msg.is_fallback ? (
                          <span className="text-amber-600 font-medium">⚡ Autonomous Fallback</span>
                        ) : (
                          <span className="text-emerald-700 font-medium">
                            📖 Grounded (Conf: {msg.rag_score})
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Markdown Explanation Body with Crisp LaTeX */}
                    <div className="p-6 text-sm text-slate-800 leading-relaxed prose max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {preprocessMarkdown(levelData.text)}
                      </ReactMarkdown>
                    </div>

                    {/* Card Footer Citations */}
                    {msg.citations && msg.citations.length > 0 && !msg.is_fallback && (
                      <div className="px-6 py-2.5 bg-slate-50/60 border-t border-slate-100 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                        <span className="font-semibold text-slate-600 flex items-center gap-1">
                          <BookOpen size={12} className="text-blue-600" />
                          Textbook Citations:
                        </span>
                        {msg.citations.map((c, cIdx) => (
                          <span key={cIdx} className="bg-white border border-slate-200 px-2 py-0.5 rounded text-[11px] font-medium text-slate-700 shadow-2xs">
                            {c.source} (Page {c.page})
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Rationale micro-badge */}
                  {msg.adaptation_reason && (
                    <div className="text-[11px] text-slate-600 italic px-2">
                      💡 Reason: {msg.adaptation_reason}
                    </div>
                  )}

                </div>
              );
            })}

            {/* Live Typing Loader */}
            {loading && (
              <div className="bg-white rounded-2xl border border-slate-200 p-5 max-w-md shadow-xs flex items-center gap-3 text-xs text-slate-500">
                <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <div>
                  <div className="font-medium text-slate-800">EduPath is analyzing query & generating all 3 levels...</div>
                  <div className="text-[11px] text-slate-600">Retrieving from ChromaDB dense index</div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-white border-t border-slate-200">
          <div className="max-w-3xl mx-auto relative flex items-center">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSendMessage()}
              placeholder={`Ask EduPath any ${currentSubjectMeta.name} question or misconception...`}
              disabled={loading}
              className="w-full bg-slate-50 border border-slate-300 focus:border-blue-500 focus:bg-white rounded-xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={loading || !input.trim()}
              className="absolute right-2.5 p-2 bg-slate-900 text-white rounded-lg hover:bg-blue-600 disabled:opacity-40 disabled:hover:bg-slate-900 transition shadow-xs"
              title="Send question"
            >
              <Send size={15} />
            </button>
          </div>
          <div className="text-center text-[11px] text-slate-500 mt-2">
            EduPath adapts explanation depth using few-shot in-context learning grounded in official NCERT textbooks.
          </div>
        </div>

      </main>

      {/* ========================================================= */}
      {/* 3. ARCHITECTURE MODAL (For Viva / Evaluation)            */}
      {/* ========================================================= */}
      {showArchModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2 font-bold text-base text-slate-900">
                <GraduationCap className="text-blue-600" />
                EduPath System Architecture & SDG 4 Impact
              </div>
              <button 
                onClick={() => setShowArchModal(false)}
                className="p-1 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-700"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4 text-xs text-slate-700 leading-relaxed">
              <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                <span className="font-semibold text-blue-900 block mb-1">🎯 Problem Solved (UN SDG 4: Quality Education)</span>
                Underserved schools suffer from severe 40:1 teacher-student ratios. EduPath delivers automated 1-on-1 tutoring, detecting student misconceptions and shifting explanations across 3 cognitive levels.
              </div>

              <div>
                <h4 className="font-bold text-slate-900 mb-1">1. Two-Stage RAG Pipeline with ChromaDB</h4>
                <ul className="list-disc pl-4 space-y-1 text-slate-600">
                  <li><strong>Dense Embeddings:</strong> <code>sentence-transformers/all-MiniLM-L6-v2</code> maps NCERT textbook chunks to a 384-dimensional dense semantic space.</li>
                  <li><strong>Vector Store:</strong> Persistent ChromaDB database with HNSW Cosine Distance indexing.</li>
                  <li><strong>Confidence Threshold (0.32):</strong> If semantic match is below 0.32, triggers autonomous fallback to prevent hallucinations.</li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold text-slate-900 mb-1">2. LangGraph Stateful Agent Workflow</h4>
                <ul className="list-disc pl-4 space-y-1 text-slate-600">
                  <li><strong>Assess Node:</strong> Diagnoses misconceptions and calibrates active cognitive level.</li>
                  <li><strong>Retrieve Node:</strong> Queries ChromaDB with subject metadata filtering.</li>
                  <li><strong>Generate Node:</strong> Injects tailored few-shot pedagogical exemplars for Level 1, 2, and 3.</li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold text-slate-900 mb-1">3. ChatGPT-Style Multi-Level UX Innovation</h4>
                <p className="text-slate-600">
                  Generates Level 1 (Foundational), Level 2 (Conceptual), and Level 3 (Socratic) concurrently, allowing students to toggle explanation styles on-the-fly with zero latency.
                </p>
              </div>
            </div>

            <div className="pt-2 text-right">
              <button
                onClick={() => setShowArchModal(false)}
                className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
