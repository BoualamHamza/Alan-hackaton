'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Loader2, Bot, User, BookOpen, Paperclip, ChevronDown } from 'lucide-react';

const ASSISTANT_URL = process.env.NEXT_PUBLIC_ASSISTANT_URL ?? 'http://localhost:8001';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
}

// ── Markdown-lite renderer (bold, lists) ─────────────────────────────────────
function MessageContent({ text }: { text: string }) {
  // Split into paragraphs, then render bold (**text**) and bullets
  const paragraphs = text.split(/\n\n+/);
  return (
    <div className="space-y-2 text-sm leading-relaxed">
      {paragraphs.map((para, i) => {
        const lines = para.split('\n');
        const isList = lines.every((l) => /^[-*•]|\d+\./.test(l.trim()) || l.trim() === '');
        if (isList && lines.length > 1) {
          return (
            <ul key={i} className="space-y-1 pl-1">
              {lines.filter(Boolean).map((line, j) => (
                <li key={j} className="flex items-start gap-2">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                  <span dangerouslySetInnerHTML={{ __html: renderInline(line.replace(/^[-*•]\s*|\d+\.\s*/, '')) }} />
                </li>
              ))}
            </ul>
          );
        }
        return (
          <p key={i} dangerouslySetInnerHTML={{ __html: renderInline(para) }} />
        );
      })}
    </div>
  );
}

function renderInline(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>');
}

// ── Suggested starter questions ──────────────────────────────────────────────
const SUGGESTIONS = [
  'What are common side effects of Metformin?',
  'How does Amlodipine lower blood pressure?',
  'What does an HbA1c level of 8% mean?',
  'What should I eat to manage hypertension?',
];

export default function AIAssistant() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Focus input when panel opens
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 150);
  }, [open]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setShowSuggestions(false);
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: trimmed }]);
    setLoading(true);

    try {
      const res = await fetch(`${ASSISTANT_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, session_id: sessionId }),
      });

      if (!res.ok) throw new Error('Request failed');
      const data = await res.json();

      setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response, sources: data.sources },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: "I'm sorry, I couldn't connect to the assistant right now. Please try again.", sources: [] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const clearChat = async () => {
    if (sessionId) {
      await fetch(`${ASSISTANT_URL}/chat/${sessionId}`, { method: 'DELETE' }).catch(() => null);
    }
    setMessages([]);
    setSessionId(null);
    setShowSuggestions(true);
  };

  return (
    <>
      {/* ── Floating trigger button ── */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl shadow-lg shadow-blue-200 transition-all hover:scale-105 active:scale-95"
        >
          <div className="relative">
            <Bot size={20} />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-white" />
          </div>
          <span className="text-sm font-semibold">Ask MedBridge AI</span>
        </button>
      )}

      {/* ── Chat panel ── */}
      {open && (
        <div className="fixed bottom-6 right-6 z-50 w-[400px] max-w-[calc(100vw-24px)] flex flex-col bg-white rounded-2xl shadow-2xl shadow-slate-200/80 border border-slate-200 overflow-hidden"
             style={{ height: 'min(620px, calc(100vh - 48px))' }}>

          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3.5 bg-blue-600 text-white flex-shrink-0">
            <div className="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center flex-shrink-0">
              <Bot size={17} className="text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold leading-none">MedBridge AI</p>
              <p className="text-[11px] text-blue-200 mt-0.5">Powered by Mistral + MedlinePlus</p>
            </div>
            <div className="flex items-center gap-1">
              {messages.length > 0 && (
                <button
                  onClick={clearChat}
                  className="px-2.5 py-1 text-[11px] font-medium text-blue-200 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                >
                  Clear
                </button>
              )}
              <button
                onClick={() => setOpen(false)}
                className="w-7 h-7 flex items-center justify-center hover:bg-white/10 rounded-lg transition-colors"
              >
                <ChevronDown size={16} />
              </button>
            </div>
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0">

            {/* Welcome state */}
            {messages.length === 0 && (
              <div className="flex flex-col items-center text-center pt-4 pb-2">
                <div className="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center mb-3">
                  <Bot size={28} className="text-blue-500" />
                </div>
                <p className="text-sm font-semibold text-slate-800 mb-1">Your personal health assistant</p>
                <p className="text-xs text-slate-500 max-w-[260px]">
                  Ask me anything about your medications, symptoms, or diagnosis. I use MedlinePlus to give you accurate, reliable answers.
                </p>
              </div>
            )}

            {/* Suggestion chips */}
            {showSuggestions && messages.length === 0 && (
              <div className="space-y-2">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Suggested questions</p>
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => sendMessage(s)}
                    className="w-full text-left text-xs text-slate-600 px-3 py-2.5 bg-slate-50 hover:bg-blue-50 hover:text-blue-700 border border-slate-200 hover:border-blue-200 rounded-xl transition-all"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            {/* Messages */}
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Avatar */}
                <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  msg.role === 'user' ? 'bg-blue-600' : 'bg-slate-100 border border-slate-200'
                }`}>
                  {msg.role === 'user'
                    ? <User size={13} className="text-white" />
                    : <Bot size={13} className="text-slate-500" />}
                </div>

                <div className={`flex flex-col gap-1.5 max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  {/* Bubble */}
                  <div className={`px-3.5 py-2.5 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-tr-sm'
                      : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-tl-sm'
                  }`}>
                    {msg.role === 'user'
                      ? <p className="text-sm">{msg.content}</p>
                      : <MessageContent text={msg.content} />}
                  </div>

                  {/* Sources */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <BookOpen size={10} className="text-slate-400" />
                      {msg.sources.slice(0, 3).map((src) => (
                        <span key={src} className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded-full">
                          {src}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Loading indicator */}
            {loading && (
              <div className="flex gap-2.5">
                <div className="w-7 h-7 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center flex-shrink-0">
                  <Bot size={13} className="text-slate-500" />
                </div>
                <div className="px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-sm">
                  <div className="flex gap-1 items-center">
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input area */}
          <div className="flex-shrink-0 border-t border-slate-100 p-3">
            <div className="flex items-end gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100 transition-all">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your medications, diagnosis…"
                rows={1}
                className="flex-1 text-sm text-slate-800 bg-transparent resize-none outline-none placeholder:text-slate-400 max-h-28 leading-relaxed"
                style={{ scrollbarWidth: 'none' }}
              />
              <button
                onClick={() => sendMessage(input)}
                disabled={!input.trim() || loading}
                className="w-8 h-8 flex items-center justify-center bg-blue-600 disabled:bg-slate-200 text-white disabled:text-slate-400 rounded-lg transition-all hover:bg-blue-700 active:scale-95 flex-shrink-0"
              >
                {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
              </button>
            </div>
            <p className="text-[10px] text-slate-400 text-center mt-2">
              For informational purposes only — always consult your doctor
            </p>
          </div>
        </div>
      )}
    </>
  );
}
