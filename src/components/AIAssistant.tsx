'use client';

import { useState, useRef, useEffect } from 'react';
import { X, Send, Loader2, Sparkles, BookOpen } from 'lucide-react';

const ASSISTANT_URL = process.env.NEXT_PUBLIC_ASSISTANT_URL ?? 'http://localhost:8001';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
}

interface AIAssistantProps {
  open: boolean;
  onClose: () => void;
}

// ── Markdown-lite renderer (bold, lists) ─────────────────────────────────────
function MessageContent({ text }: { text: string }) {
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
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-hippo-pink-hot flex-shrink-0" />
                  <span dangerouslySetInnerHTML={{ __html: renderInline(line.replace(/^[-*•]\s*|\d+\.\s*/, '')) }} />
                </li>
              ))}
            </ul>
          );
        }
        return <p key={i} dangerouslySetInnerHTML={{ __html: renderInline(para) }} />;
      })}
    </div>
  );
}

function renderInline(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>');
}

const SUGGESTIONS = [
  'What are common side effects of Metformin?',
  'How does Amlodipine lower blood pressure?',
  'What does an HbA1c level of 8% mean?',
  'What should I eat to manage hypertension?',
];

export default function AIAssistant({ open, onClose }: AIAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 150);
  }, [open]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

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
        {
          role: 'assistant',
          content: "I'm sorry, I couldn't reach the assistant right now. Please try again.",
          sources: [],
        },
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
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div
        className="w-full max-w-md h-[85vh] bg-white rounded-t-[32px] overflow-hidden flex flex-col animate-[slideUp_0.3s_ease-out]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-4 bg-gradient-to-r from-hippo-pink to-hippo-pink-hot text-white flex-shrink-0">
          <div className="w-11 h-11 rounded-2xl bg-white/25 flex items-center justify-center flex-shrink-0">
            <Sparkles size={20} className="text-white" strokeWidth={2.5} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-base font-bold leading-tight">Hippo AI</p>
            <p className="text-[11px] text-white/80">Powered by Mistral + MedlinePlus</p>
          </div>
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="px-3 py-1.5 text-[11px] font-bold text-white bg-white/20 hover:bg-white/30 rounded-full transition-colors"
            >
              Clear
            </button>
          )}
          <button
            onClick={onClose}
            className="w-9 h-9 flex items-center justify-center bg-white/20 hover:bg-white/30 rounded-full transition-colors"
            aria-label="Close chat"
          >
            <X size={18} />
          </button>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4 min-h-0 bg-hippo-pink-soft/30">
          {messages.length === 0 && (
            <div className="flex flex-col items-center text-center pt-4 pb-2">
              <div className="w-16 h-16 rounded-3xl bg-white shadow-[0_8px_24px_-6px_rgba(244,140,186,0.4)] flex items-center justify-center mb-4">
                <Sparkles size={28} className="text-hippo-pink-hot" strokeWidth={2.5} />
              </div>
              <p className="text-base font-bold text-hippo-ink mb-1">Hey Emma, I&apos;m Hippo</p>
              <p className="text-xs text-hippo-ink-soft max-w-[280px]">
                Ask me anything about your medications, symptoms, or diagnosis. I use MedlinePlus to give you accurate, reliable answers.
              </p>
            </div>
          )}

          {messages.length === 0 && (
            <div className="space-y-2">
              <p className="text-[11px] font-bold text-hippo-ink-soft uppercase tracking-wider">Suggested questions</p>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="w-full text-left text-xs font-medium text-hippo-ink px-4 py-3 bg-white rounded-2xl shadow-[0_4px_14px_-6px_rgba(244,140,186,0.3)] active:scale-[0.98] transition-transform"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  msg.role === 'user'
                    ? 'bg-hippo-ink text-white'
                    : 'bg-white shadow-sm'
                }`}
              >
                {msg.role === 'user' ? (
                  <span className="text-xs font-bold">E</span>
                ) : (
                  <Sparkles size={14} className="text-hippo-pink-hot" strokeWidth={2.5} />
                )}
              </div>
              <div className={`flex flex-col gap-1.5 max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div
                  className={`px-4 py-2.5 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-hippo-ink text-white rounded-tr-md'
                      : 'bg-white text-hippo-ink rounded-tl-md shadow-[0_2px_10px_-4px_rgba(244,140,186,0.3)]'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <p className="text-sm">{msg.content}</p>
                  ) : (
                    <MessageContent text={msg.content} />
                  )}
                </div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <BookOpen size={10} className="text-hippo-ink-soft" />
                    {msg.sources.slice(0, 3).map((src) => (
                      <span key={src} className="text-[10px] text-hippo-ink-soft bg-white px-2 py-0.5 rounded-full">
                        {src}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-2.5">
              <div className="w-8 h-8 rounded-full bg-white shadow-sm flex items-center justify-center flex-shrink-0">
                <Sparkles size={14} className="text-hippo-pink-hot" strokeWidth={2.5} />
              </div>
              <div className="px-4 py-3 bg-white rounded-2xl rounded-tl-md shadow-sm">
                <div className="flex gap-1 items-center">
                  <span className="w-1.5 h-1.5 bg-hippo-pink-hot rounded-full animate-bounce" />
                  <span className="w-1.5 h-1.5 bg-hippo-pink-hot rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 bg-hippo-pink-hot rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input area */}
        <div className="flex-shrink-0 px-5 py-4 bg-white border-t border-hippo-pink-soft">
          <div className="flex items-end gap-2 bg-hippo-pink-soft/50 rounded-2xl px-4 py-3 focus-within:ring-2 focus-within:ring-hippo-pink-hot transition-all">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your medications…"
              rows={1}
              className="flex-1 text-sm text-hippo-ink bg-transparent resize-none outline-none placeholder:text-hippo-ink-soft max-h-28 leading-relaxed"
              style={{ scrollbarWidth: 'none' }}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || loading}
              className="w-10 h-10 flex items-center justify-center bg-hippo-pink-hot disabled:bg-hippo-pink-soft text-white disabled:text-hippo-ink-soft rounded-full transition-all active:scale-95 flex-shrink-0"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>
          <p className="text-[10px] text-hippo-ink-soft text-center mt-2">
            For informational purposes only — always consult your doctor
          </p>
        </div>
      </div>

      <style jsx>{`
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
