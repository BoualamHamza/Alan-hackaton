'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import {
  Activity, Film, BookOpen, Gamepad2, Paperclip,
  ExternalLink, AlertCircle, Upload, Mic, FileText, Eye, Trash2,
  ArrowLeft,
} from 'lucide-react';
import { mockCases } from '@/lib/mockData';
import { getCase } from '@/lib/api';
import ReelsFeed from '@/components/ReelsFeed';
import QuizGame from '@/components/QuizGame';
import MetricsPanel from '@/components/MetricsPanel';
import { MedicalCase } from '@/types';

type TabId = 'metrics' | 'reels' | 'articles' | 'game' | 'documents';

const tabs: { id: TabId; label: string; icon: React.ComponentType<{ size?: number; strokeWidth?: number }> }[] = [
  { id: 'metrics', label: 'Metrics', icon: Activity },
  { id: 'reels', label: 'Reels', icon: Film },
  { id: 'articles', label: 'Articles', icon: BookOpen },
  { id: 'game', label: 'Quiz', icon: Gamepad2 },
  { id: 'documents', label: 'Docs', icon: Paperclip },
];

export default function CaseDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();

  const caseId = params.id as string;
  const activeTab = (searchParams.get('tab') ?? 'metrics') as TabId;

  const mockCase = mockCases.find((c) => c.id === caseId);
  const [caseData, setCaseData] = useState<MedicalCase>(mockCase ?? mockCases[0]);
  const [caseLoaded, setCaseLoaded] = useState(!!mockCase);

  useEffect(() => {
    if (mockCase) return;
    getCase(caseId)
      .then((data) => { setCaseData(data); setCaseLoaded(true); })
      .catch(() => setCaseLoaded(true));
  }, [caseId]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4">
      {/* Back */}
      <Link
        href="/cases"
        className="inline-flex items-center gap-1.5 text-[12px] font-bold text-hippo-ink-soft active:text-hippo-pink-hot"
      >
        <ArrowLeft size={14} strokeWidth={3} />
        All cases
      </Link>

      {/* Case header */}
      <header className="bg-white rounded-[24px] p-5 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)]">
        <span className="inline-block text-[10px] font-bold text-hippo-pink-hot bg-hippo-pink-soft px-2.5 py-1 rounded-full uppercase tracking-wide">
          {caseData.specialty}
        </span>
        <h1 className="text-[18px] font-extrabold text-hippo-ink leading-tight mt-2">
          {caseLoaded ? caseData.title : <span className="inline-block w-48 h-5 bg-hippo-pink-soft rounded animate-pulse" />}
        </h1>
        <p className="text-[12px] text-hippo-ink-soft mt-1">
          {caseLoaded
            ? `${caseData.doctorName} · ${new Date(caseData.visitDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
            : <span className="inline-block w-36 h-3 bg-hippo-pink-soft rounded animate-pulse" />}
        </p>
      </header>

      {/* Tab scroller */}
      <div className="-mx-5 px-5 overflow-x-auto no-scrollbar">
        <div className="flex gap-2 min-w-max pb-1">
          {tabs.map(({ id, label, icon: Icon }) => {
            const active = activeTab === id;
            return (
              <Link
                key={id}
                href={`/cases/${caseId}?tab=${id}`}
                className={`flex items-center gap-1.5 px-4 py-2.5 rounded-full text-[12px] font-bold whitespace-nowrap transition-all ${
                  active
                    ? 'bg-hippo-ink text-white'
                    : 'bg-white text-hippo-ink-soft shadow-[0_4px_14px_-8px_rgba(244,140,186,0.4)]'
                }`}
              >
                <Icon size={13} strokeWidth={2.5} />
                {label}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'metrics' && <MetricsPanel specialty={caseData.specialty} />}
        {activeTab === 'reels' && <ReelsFeed caseId={caseId} />}
        {activeTab === 'game' && <QuizGame />}
        {activeTab === 'articles' && (
          <ArticlesTab caseTitle={caseData.title} specialty={caseData.specialty} symptoms={caseData.symptoms} />
        )}
        {activeTab === 'documents' && <DocumentsTab hasVoiceNote={caseData.hasVoiceNote} />}
      </div>
    </div>
  );
}

// ─── Articles (inline — calls MedlinePlus via Charlie assistant) ───────────

const ASSISTANT_URL = process.env.NEXT_PUBLIC_ASSISTANT_URL ?? 'http://localhost:8001';

interface MedArticle {
  title: string;
  url: string;
  excerpt: string;
  source: string;
}

function ArticlesTab({ caseTitle, specialty, symptoms }: { caseTitle: string; specialty: string; symptoms: string[] }) {
  const [articles, setArticles] = useState<MedArticle[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const query = [specialty, ...symptoms, caseTitle].filter(Boolean).join(' ');
    fetch(`${ASSISTANT_URL}/articles?query=${encodeURIComponent(query)}&k=5`)
      .then((r) => r.json())
      .then((data) => { setArticles(data); setLoading(false); })
      .catch(() => { setError(true); setLoading(false); });
  }, [caseTitle, specialty, symptoms.join(',')]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-3">
      {loading && [1, 2, 3].map((i) => (
        <div key={i} className="bg-white rounded-[20px] p-4 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)] animate-pulse">
          <div className="h-3 bg-hippo-pink-soft rounded w-1/4 mb-3" />
          <div className="h-4 bg-hippo-pink-soft rounded w-3/4 mb-2" />
          <div className="h-3 bg-hippo-pink-soft rounded w-full" />
        </div>
      ))}

      {error && (
        <div className="flex items-center gap-3 bg-white rounded-[20px] px-4 py-3 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)]">
          <AlertCircle size={16} className="text-amber-500 flex-shrink-0" />
          <p className="text-[12px] text-hippo-ink-soft">Could not load articles — Hippo assistant may be offline.</p>
        </div>
      )}

      {articles && articles.map((a, i) => (
        <a
          key={i}
          href={a.url || '#'}
          target="_blank"
          rel="noopener noreferrer"
          className="block bg-white rounded-[20px] p-4 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)] active:scale-[0.99] transition-transform"
        >
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-hippo-pink-soft flex items-center justify-center flex-shrink-0">
              <BookOpen size={16} className="text-hippo-pink-hot" strokeWidth={2.5} />
            </div>
            <div className="flex-1 min-w-0">
              <span className="inline-block text-[10px] font-bold text-hippo-pink-hot bg-hippo-pink-soft px-2 py-0.5 rounded-full uppercase tracking-wide">
                {a.source}
              </span>
              <h4 className="text-[13px] font-bold text-hippo-ink leading-snug mt-1.5">
                {a.title}
              </h4>
              <p className="text-[11px] text-hippo-ink-soft leading-relaxed line-clamp-2 mt-1">{a.excerpt}</p>
              <div className="flex items-center gap-1 mt-2 text-[10px] font-bold text-hippo-pink-hot">
                <ExternalLink size={10} strokeWidth={3} />
                Read on MedlinePlus
              </div>
            </div>
          </div>
        </a>
      ))}
    </div>
  );
}

// ─── Documents ─────────────────────────────────────────────────────────────

function DocumentsTab({ hasVoiceNote }: { hasVoiceNote: boolean }) {
  const [dragOver, setDragOver] = useState(false);
  const [files, setFiles] = useState([
    { name: 'MRI_Report_April2026.pdf', size: '2.4 MB', date: 'Apr 8', category: 'Imaging' },
    { name: 'Prescription_Mitchell.pdf', size: '180 KB', date: 'Apr 8', category: 'Prescription' },
    { name: 'Lab_Results_March.pdf', size: '540 KB', date: 'Mar 22', category: 'Lab Results' },
  ]);

  const categoryColor: Record<string, string> = {
    Imaging: 'bg-purple-100 text-purple-700',
    Prescription: 'bg-hippo-pink-soft text-hippo-pink-hot',
    'Lab Results': 'bg-amber-100 text-amber-700',
    Other: 'bg-slate-100 text-slate-600',
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const newFiles = Array.from(e.dataTransfer.files).map((f) => ({
      name: f.name,
      size: `${(f.size / 1024).toFixed(0)} KB`,
      date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      category: 'Other',
    }));
    setFiles((prev) => [...newFiles, ...prev]);
  };

  const removeFile = (name: string) => setFiles((prev) => prev.filter((f) => f.name !== name));

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`rounded-[24px] p-5 flex items-center gap-4 transition-all ${
          dragOver
            ? 'bg-hippo-pink-soft ring-2 ring-hippo-pink-hot'
            : 'bg-white shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)]'
        }`}
      >
        <div className="w-12 h-12 rounded-2xl bg-hippo-pink-soft flex items-center justify-center flex-shrink-0">
          <Upload size={20} className="text-hippo-pink-hot" strokeWidth={2.5} />
        </div>
        <div>
          <p className="text-[13px] font-bold text-hippo-ink">Upload files</p>
          <p className="text-[11px] text-hippo-ink-soft mt-0.5">PDF, JPG, PNG — up to 10 MB</p>
        </div>
      </div>

      {hasVoiceNote && (
        <div className="bg-gradient-to-br from-hippo-pink to-hippo-pink-hot rounded-[24px] p-4 flex items-center gap-3 text-white">
          <div className="w-10 h-10 rounded-2xl bg-white/25 flex items-center justify-center flex-shrink-0">
            <Mic size={16} />
          </div>
          <div className="flex-1">
            <p className="text-[13px] font-bold">Voice note recorded</p>
            <p className="text-[11px] opacity-80">1:24 · tap to play</p>
          </div>
          <button className="px-4 py-2 bg-white/25 rounded-full text-[11px] font-bold">Play</button>
        </div>
      )}

      <div className="space-y-2">
        {files.map((file) => (
          <div
            key={file.name}
            className="flex items-center gap-3 bg-white rounded-[18px] px-4 py-3 shadow-[0_4px_16px_-10px_rgba(244,140,186,0.4)]"
          >
            <div className="w-10 h-10 rounded-xl bg-hippo-pink-soft flex items-center justify-center flex-shrink-0">
              <FileText size={16} className="text-hippo-pink-hot" strokeWidth={2.5} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[12px] font-bold text-hippo-ink truncate">{file.name}</p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${categoryColor[file.category] ?? categoryColor.Other}`}>
                  {file.category}
                </span>
                <span className="text-[10px] text-hippo-ink-soft">{file.size} · {file.date}</span>
              </div>
            </div>
            <button className="p-2 text-hippo-ink-soft active:text-hippo-pink-hot" aria-label="Preview">
              <Eye size={14} />
            </button>
            <button
              onClick={() => removeFile(file.name)}
              className="p-2 text-hippo-ink-soft active:text-red-500"
              aria-label="Remove"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
