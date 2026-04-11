'use client';

import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import {
  Activity, Play, Calendar, BookOpen,
  Gamepad2, Upload, TrendingUp, TrendingDown,
  Minus, Clock, FileText, ExternalLink, CheckSquare, Square,
  Star, Zap, Heart, Brain, Dumbbell, Apple, ChevronRight,
  Paperclip, Mic, Trash2, Eye, Loader2, AlertCircle, Video
} from 'lucide-react';
import { mockCases } from '@/lib/mockData';
import { getCase, API_BASE } from '@/lib/api';
import { VideoStatus, VideoInfo } from '@/types';

type TabId = 'analytics' | 'videos' | 'calendar' | 'articles' | 'game' | 'documents' | 'import';

const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'analytics', label: 'Analytics', icon: <Activity size={16} /> },
  { id: 'videos', label: 'Videos', icon: <Play size={16} /> },
  { id: 'calendar', label: 'Calendar', icon: <Calendar size={16} /> },
  { id: 'articles', label: 'Articles', icon: <BookOpen size={16} /> },
  { id: 'game', label: 'Game', icon: <Gamepad2 size={16} /> },
  { id: 'documents', label: 'Documents', icon: <Paperclip size={16} /> },
  { id: 'import', label: 'Import Data', icon: <Upload size={16} /> },
];

// ─── Tab content components ────────────────────────────────────────────────

function AnalyticsTab({ specialty }: { specialty: string }) {
  const metrics = [
    { label: 'Pain Level', value: '4/10', trend: 'down', change: '−2 from last visit', color: 'text-emerald-600' },
    { label: 'Sleep Quality', value: '6.5h', trend: 'up', change: '+1h avg', color: 'text-blue-600' },
    { label: 'Activity Score', value: '72%', trend: 'up', change: '+8% this week', color: 'text-blue-600' },
    { label: 'Medication Adherence', value: '89%', trend: 'stable', change: 'Consistent', color: 'text-slate-600' },
  ];

  const timeline = [
    { date: 'Apr 8', event: 'Consultation', note: 'Initial diagnosis, MRI ordered' },
    { date: 'Apr 15', event: 'MRI Scan', note: 'Results pending' },
    { date: 'Apr 22', event: 'Follow-up', note: 'Review MRI results' },
    { date: 'May 10', event: 'PT Session 1', note: 'Physical therapy begins' },
  ];

  const trendIcon = (t: string) =>
    t === 'up' ? <TrendingUp size={14} className="text-emerald-500" /> :
    t === 'down' ? <TrendingDown size={14} className="text-red-400" /> :
    <Minus size={14} className="text-slate-400" />;

  return (
    <div className="space-y-6">
      {/* Key metrics */}
      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Key Health Metrics</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {metrics.map((m) => (
            <div key={m.label} className="bg-white rounded-xl border border-slate-200 p-4">
              <p className="text-xs text-slate-500 mb-2">{m.label}</p>
              <p className={`text-2xl font-bold mb-1 ${m.color}`}>{m.value}</p>
              <div className="flex items-center gap-1">
                {trendIcon(m.trend)}
                <span className="text-xs text-slate-400">{m.change}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Mini chart placeholder */}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-slate-700">Symptom Trend (last 30 days)</h3>
          <span className="text-xs text-slate-400">Apr 2026</span>
        </div>
        <div className="flex items-end gap-1.5 h-24">
          {[7, 6, 8, 5, 7, 4, 6, 5, 4, 4, 5, 3, 4, 3].map((v, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-1">
              <div
                className="w-full rounded-t-sm bg-blue-200 transition-all"
                style={{ height: `${(v / 10) * 100}%` }}
              />
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2">
          <span className="text-xs text-slate-400">Mar 28</span>
          <span className="text-xs text-slate-400">Apr 10</span>
        </div>
      </div>

      {/* Care timeline */}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-sm font-semibold text-slate-700 mb-4">Care Timeline</h3>
        <div className="space-y-0">
          {timeline.map((item, i) => (
            <div key={i} className="flex gap-4">
              <div className="flex flex-col items-center">
                <div className="w-2.5 h-2.5 rounded-full bg-blue-500 mt-1 flex-shrink-0" />
                {i < timeline.length - 1 && <div className="w-px flex-1 bg-slate-200 my-1" />}
              </div>
              <div className="pb-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-blue-600">{item.date}</span>
                  <span className="text-sm font-medium text-slate-800">{item.event}</span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">{item.note}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Insight */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-5">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0">
            <Zap size={15} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold text-blue-900 mb-1">AI Health Insight</p>
            <p className="text-sm text-blue-700 leading-relaxed">
              Based on your {specialty} case, your symptoms show a gradual improvement trend over the past 2 weeks.
              Maintaining your current physical therapy routine and medication schedule appears to be effective.
              Consider logging your daily pain levels for more accurate tracking.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Video polling hook ────────────────────────────────────────────────────────

// Mock case IDs are like "case-1"; real backend cases have UUIDs
const isMockCase = (id: string) => mockCases.some((c) => c.id === id);

function useVideoPolling(caseId: string) {
  const [videoStatus, setVideoStatus] = useState<VideoStatus | undefined>(
    isMockCase(caseId) ? undefined : undefined  // unified start; mock cases detected below
  );
  const [videos, setVideos] = useState<VideoInfo[] | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isMock] = useState(() => isMockCase(caseId));

  useEffect(() => {
    if (isMock) return; // mock cases have no backend data — skip polling

    let cancelled = false;

    const poll = async () => {
      try {
        const data = await getCase(caseId);
        if (cancelled) return;
        setVideoStatus(data.videoStatus);
        setVideos(data.videos ?? null);
        setErrorMessage(data.errorMessage ?? null);
      } catch {
        // network error — keep polling
      }
    };

    poll(); // immediate first check
    const interval = setInterval(() => {
      if (videoStatus === 'ready' || videoStatus === 'error') return;
      poll();
    }, 5000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId, videoStatus]);

  return { videoStatus, videos, errorMessage, isMock };
}

// ── Videos sub-components ─────────────────────────────────────────────────────

function VideosLoading() {
  return (
    <div className="space-y-5">
      {/* Banner */}
      <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-xl px-5 py-4">
        <Loader2 size={18} className="text-blue-600 animate-spin mt-0.5 flex-shrink-0" />
        <div>
          <p className="text-sm font-semibold text-blue-900">Generating your personalised videos…</p>
          <p className="text-xs text-blue-600 mt-0.5">
            We're creating two AI videos tailored to your consultation. This takes 2–5 minutes.
            No need to refresh — they'll appear here automatically.
          </p>
        </div>
      </div>
      {/* Skeleton cards */}
      {[0, 1].map((i) => (
        <div key={i} className="bg-white rounded-xl border border-slate-200 overflow-hidden animate-pulse">
          <div className="h-48 bg-slate-100" />
          <div className="p-4 space-y-2">
            <div className="h-3 bg-slate-100 rounded w-1/3" />
            <div className="h-4 bg-slate-200 rounded w-3/4" />
            <div className="h-3 bg-slate-100 rounded w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

function VideosReady({ caseId, videos }: { caseId: string; videos: VideoInfo[] }) {
  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-500">
        Your personalised AI videos are ready. These were generated specifically based on your consultation.
      </p>
      {videos.map((v, idx) => (
        <div key={v.id} className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <video
            controls
            preload="metadata"
            className="w-full"
            src={`${API_BASE}/cases/${caseId}/videos/${idx + 1}`}
          >
            Your browser does not support video playback.
          </video>
          <div className="px-4 py-3 border-t border-slate-100">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-blue-100 flex items-center justify-center">
                <Video size={12} className="text-blue-600" />
              </div>
              <p className="text-sm font-semibold text-slate-800">{v.title}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function VideosError({ errorMessage }: { errorMessage: string | null }) {
  return (
    <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-5 py-4">
      <AlertCircle size={18} className="text-red-500 mt-0.5 flex-shrink-0" />
      <div>
        <p className="text-sm font-semibold text-red-800">Video generation failed</p>
        {errorMessage && (
          <p className="text-xs text-red-600 mt-1 font-mono">{errorMessage}</p>
        )}
        <p className="text-xs text-red-500 mt-1">Please try creating the case again.</p>
      </div>
    </div>
  );
}

function VideosTab({ caseId }: { caseId: string }) {
  const { videoStatus, videos, errorMessage, isMock } = useVideoPolling(caseId);

  // Mock cases have no backend videos
  if (isMock) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-slate-500">
          Curated videos to help you better understand your condition and treatment.
        </p>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
            <Video size={24} className="text-slate-300" />
          </div>
          <p className="text-sm font-medium text-slate-600 mb-1">No videos yet</p>
          <p className="text-xs text-slate-400 max-w-xs">
            Videos are generated automatically when you create a new case via the form.
          </p>
        </div>
      </div>
    );
  }

  // Still fetching initial status from backend
  if (videoStatus === undefined || videoStatus === 'pending' || videoStatus === 'processing') {
    return <VideosLoading />;
  }

  if (videoStatus === 'error') {
    return <VideosError errorMessage={errorMessage} />;
  }

  if (videoStatus === 'ready' && videos && videos.length > 0) {
    return <VideosReady caseId={caseId} videos={videos} />;
  }

  return <VideosLoading />;
}

function CalendarTab() {
  const today = new Date();
  const month = today.toLocaleString('default', { month: 'long', year: 'numeric' });

  const events = [
    { date: 15, label: 'MRI Scan', type: 'appointment', time: '9:00 AM' },
    { date: 18, label: 'PT Session', type: 'therapy', time: '2:30 PM' },
    { date: 22, label: 'Follow-up', type: 'appointment', time: '11:00 AM' },
    { date: 25, label: 'PT Session', type: 'therapy', time: '2:30 PM' },
    { date: 28, label: 'Medication Review', type: 'reminder', time: '—' },
  ];

  const typeConfig: Record<string, { color: string; dot: string }> = {
    appointment: { color: 'bg-blue-50 text-blue-700 border-blue-200', dot: 'bg-blue-500' },
    therapy: { color: 'bg-emerald-50 text-emerald-700 border-emerald-200', dot: 'bg-emerald-500' },
    reminder: { color: 'bg-amber-50 text-amber-700 border-amber-200', dot: 'bg-amber-500' },
  };

  // Mini calendar grid
  const daysInMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1).getDay();
  const eventDays = new Set(events.map((e) => e.date));

  const cells = [
    ...Array(firstDay).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  return (
    <div className="space-y-6">
      {/* Calendar */}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-slate-700">{month}</h3>
          <div className="flex gap-1">
            <button className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors">
              <ChevronRight size={14} className="text-slate-400 rotate-180" />
            </button>
            <button className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors">
              <ChevronRight size={14} className="text-slate-400" />
            </button>
          </div>
        </div>
        <div className="grid grid-cols-7 gap-1">
          {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map((d) => (
            <div key={d} className="text-center text-xs font-medium text-slate-400 py-1">{d}</div>
          ))}
          {cells.map((day, i) => (
            <div
              key={i}
              className={`aspect-square flex flex-col items-center justify-center rounded-lg text-xs transition-all ${
                day === null
                  ? ''
                  : day === today.getDate()
                  ? 'bg-blue-600 text-white font-semibold'
                  : eventDays.has(day as number)
                  ? 'bg-blue-50 text-blue-700 font-medium cursor-pointer hover:bg-blue-100'
                  : 'text-slate-600 hover:bg-slate-50 cursor-pointer'
              }`}
            >
              {day}
              {day !== null && eventDays.has(day as number) && day !== today.getDate() && (
                <span className="w-1 h-1 rounded-full bg-blue-500 mt-0.5" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Upcoming events */}
      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Upcoming Events</h3>
        <div className="space-y-2">
          {events.map((ev, i) => {
            const cfg = typeConfig[ev.type];
            return (
              <div
                key={i}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${cfg.color} transition-all hover:shadow-sm`}
              >
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${cfg.dot}`} />
                <div className="flex-1">
                  <p className="text-sm font-medium">{ev.label}</p>
                  <p className="text-xs opacity-70 mt-0.5">April {ev.date} · {ev.time}</p>
                </div>
                <Clock size={13} className="opacity-50" />
              </div>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-slate-500">
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-blue-500" />Appointments</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500" />Therapy</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-500" />Reminders</span>
      </div>
    </div>
  );
}

function ArticlesTab({ specialty }: { specialty: string }) {
  const articles = [
    {
      title: `Living with ${specialty} Conditions: A Complete Patient Guide`,
      source: 'Mayo Clinic',
      readTime: '8 min read',
      date: 'Apr 2026',
      excerpt: 'Comprehensive overview of managing your condition day-to-day, including lifestyle modifications, treatment adherence, and mental health considerations.',
      tags: ['Patient Guide', 'Lifestyle'],
      icon: '📖',
    },
    {
      title: 'Understanding Your Diagnosis: Key Questions to Ask Your Doctor',
      source: 'Harvard Health',
      readTime: '5 min read',
      date: 'Mar 2026',
      excerpt: 'Before your next appointment, prepare yourself with the right questions to ensure you fully understand your diagnosis and treatment plan.',
      tags: ['Communication', 'Doctors'],
      icon: '❓',
    },
    {
      title: 'Nutrition and Recovery: Evidence-Based Dietary Strategies',
      source: 'Cleveland Clinic',
      readTime: '12 min read',
      date: 'Apr 2026',
      excerpt: 'Learn which foods support healing and which may exacerbate symptoms, backed by current clinical research.',
      tags: ['Nutrition', 'Research'],
      icon: '🥦',
    },
    {
      title: 'The Role of Exercise in Managing Chronic Conditions',
      source: 'WebMD',
      readTime: '7 min read',
      date: 'Mar 2026',
      excerpt: 'Physical activity can significantly improve outcomes for many chronic conditions. Here\'s how to get started safely.',
      tags: ['Exercise', 'Wellness'],
      icon: '🏃',
    },
  ];

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">
        Evidence-based articles curated to help you understand and manage your health.
      </p>
      {articles.map((a, i) => (
        <div
          key={i}
          className="bg-white rounded-xl border border-slate-200 p-5 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex items-start gap-4">
            <div className="text-2xl mt-0.5">{a.icon}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                {a.tags.map((tag) => (
                  <span key={tag} className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                    {tag}
                  </span>
                ))}
              </div>
              <h4 className="text-sm font-semibold text-slate-900 mb-2 group-hover:text-blue-700 transition-colors leading-snug">
                {a.title}
              </h4>
              <p className="text-sm text-slate-500 leading-relaxed mb-3 line-clamp-2">{a.excerpt}</p>
              <div className="flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center gap-3">
                  <span className="font-medium text-slate-600">{a.source}</span>
                  <span>·</span>
                  <span>{a.readTime}</span>
                  <span>·</span>
                  <span>{a.date}</span>
                </div>
                <ExternalLink size={12} className="group-hover:text-blue-500 transition-colors" />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function GameTab() {
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState<number[]>([]);
  const [selected, setSelected] = useState<{ qIdx: number; aIdx: number } | null>(null);

  const questions = [
    {
      q: 'What does "chronic" mean in a medical diagnosis?',
      options: ['Severe and sudden', 'Long-lasting, 3+ months', 'Contagious', 'Only affecting older patients'],
      correct: 1,
      explanation: 'Chronic conditions persist for 3 months or longer, as opposed to acute conditions which are short-term.',
    },
    {
      q: 'What is the purpose of an MRI scan?',
      options: ['Measure blood pressure', 'Create detailed images of soft tissues', 'Test blood sugar', 'Check heart rhythm'],
      correct: 1,
      explanation: 'MRI (Magnetic Resonance Imaging) uses magnetic fields to create detailed images of soft tissues, organs, and bones.',
    },
    {
      q: 'What does "HbA1c" measure?',
      options: ['Blood pressure over time', 'Average blood sugar over 3 months', 'Cholesterol levels', 'Liver function'],
      correct: 1,
      explanation: 'HbA1c (glycated hemoglobin) reflects your average blood glucose levels over the past 2-3 months.',
    },
  ];

  const handleAnswer = (qIdx: number, aIdx: number) => {
    if (answered.includes(qIdx)) return;
    setSelected({ qIdx, aIdx });
    if (aIdx === questions[qIdx].correct) {
      setScore((s) => s + 10);
    }
    setTimeout(() => {
      setAnswered((prev) => [...prev, qIdx]);
      setSelected(null);
    }, 1500);
  };

  const progress = (answered.length / questions.length) * 100;

  return (
    <div className="space-y-6">
      {/* Score bar */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-5 text-white">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-sm opacity-80 mb-0.5">Health Knowledge Quiz</p>
            <p className="text-2xl font-bold">{score} pts</p>
          </div>
          <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
            <Star size={22} className="text-yellow-300" />
          </div>
        </div>
        <div className="bg-white/20 rounded-full h-2">
          <div
            className="bg-white rounded-full h-2 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs opacity-70 mt-1.5">{answered.length}/{questions.length} questions answered</p>
      </div>

      {/* Questions */}
      <div className="space-y-4">
        {questions.map((q, qIdx) => {
          const isDone = answered.includes(qIdx);
          return (
            <div key={qIdx} className={`bg-white rounded-xl border p-5 transition-all ${isDone ? 'border-slate-200 opacity-75' : 'border-slate-200'}`}>
              <p className="text-sm font-semibold text-slate-900 mb-3">{q.q}</p>
              <div className="space-y-2">
                {q.options.map((opt, aIdx) => {
                  const isSel = selected?.qIdx === qIdx && selected.aIdx === aIdx;
                  const isCorrect = q.correct === aIdx;
                  let className = 'flex items-center gap-3 px-3.5 py-2.5 rounded-lg border text-sm transition-all cursor-pointer ';

                  if (isDone) {
                    className += isCorrect
                      ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                      : 'border-slate-200 text-slate-400';
                  } else if (isSel) {
                    className += isCorrect
                      ? 'border-emerald-400 bg-emerald-50 text-emerald-700'
                      : 'border-red-400 bg-red-50 text-red-700';
                  } else {
                    className += 'border-slate-200 text-slate-700 hover:border-blue-300 hover:bg-blue-50';
                  }

                  return (
                    <div key={aIdx} className={className} onClick={() => handleAnswer(qIdx, aIdx)}>
                      {isDone ? (
                        isCorrect ? <CheckSquare size={15} className="text-emerald-500 flex-shrink-0" /> : <Square size={15} className="text-slate-300 flex-shrink-0" />
                      ) : (
                        <div className="w-4 h-4 rounded border border-current opacity-40 flex-shrink-0" />
                      )}
                      {opt}
                    </div>
                  );
                })}
              </div>
              {isDone && (
                <div className="mt-3 px-3 py-2 bg-slate-50 rounded-lg text-xs text-slate-600">
                  <span className="font-medium">Explanation: </span>{q.explanation}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {answered.length === questions.length && (
        <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl border border-emerald-200 p-5 text-center">
          <p className="text-lg font-bold text-emerald-700 mb-1">Quiz Complete!</p>
          <p className="text-sm text-emerald-600">
            You scored {score}/{questions.length * 10} points. Great job learning about your health!
          </p>
          <button
            onClick={() => { setScore(0); setAnswered([]); setSelected(null); }}
            className="mt-3 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors"
          >
            Play Again
          </button>
        </div>
      )}
    </div>
  );
}

function DocumentsTab() {
  const [dragOver, setDragOver] = useState(false);
  const [files, setFiles] = useState([
    { name: 'MRI_Report_April2026.pdf', type: 'pdf', size: '2.4 MB', date: 'Apr 8, 2026', category: 'Imaging' },
    { name: 'Prescription_Mitchell.pdf', type: 'pdf', size: '180 KB', date: 'Apr 8, 2026', category: 'Prescription' },
    { name: 'Lab_Results_March.pdf', type: 'pdf', size: '540 KB', date: 'Mar 22, 2026', category: 'Lab Results' },
  ]);

  const categoryColors: Record<string, string> = {
    'Imaging': 'bg-purple-100 text-purple-700',
    'Prescription': 'bg-blue-100 text-blue-700',
    'Lab Results': 'bg-amber-100 text-amber-700',
    'Other': 'bg-slate-100 text-slate-600',
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const newFiles = Array.from(e.dataTransfer.files).map((f) => ({
      name: f.name,
      type: f.name.split('.').pop() ?? 'file',
      size: `${(f.size / 1024).toFixed(0)} KB`,
      date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      category: 'Other',
    }));
    setFiles((prev) => [...newFiles, ...prev]);
  };

  const removeFile = (name: string) => setFiles((prev) => prev.filter((f) => f.name !== name));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-slate-900 mb-1">Consultation Documents</h2>
        <p className="text-sm text-slate-500">Files you uploaded during case creation, plus any you add here.</p>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-6 flex items-center gap-4 cursor-pointer transition-all ${
          dragOver ? 'border-blue-400 bg-blue-50' : 'border-slate-200 hover:border-slate-300 bg-white'
        }`}
      >
        <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center flex-shrink-0">
          <Upload size={18} className="text-slate-400" />
        </div>
        <div>
          <p className="text-sm font-medium text-slate-700">Drop files here or click to upload</p>
          <p className="text-xs text-slate-400 mt-0.5">PDF, JPG, PNG, DOCX — up to 10 MB each</p>
        </div>
      </div>

      {/* Voice note if present */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
          <Mic size={14} className="text-white" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-blue-900">Voice note recorded</p>
          <p className="text-xs text-blue-500 mt-0.5">Recorded during case creation · 1:24</p>
        </div>
        <button className="text-xs text-blue-600 font-medium hover:underline">Play</button>
      </div>

      {/* File list */}
      {files.length > 0 ? (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            {files.length} document{files.length !== 1 ? 's' : ''}
          </p>
          {files.map((file) => (
            <div
              key={file.name}
              className="flex items-center gap-3.5 bg-white rounded-xl border border-slate-200 px-4 py-3 hover:border-slate-300 transition-all group"
            >
              <div className="w-9 h-9 rounded-lg bg-red-50 border border-red-100 flex items-center justify-center flex-shrink-0">
                <FileText size={16} className="text-red-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-800 truncate">{file.name}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${categoryColors[file.category] ?? categoryColors['Other']}`}>
                    {file.category}
                  </span>
                  <span className="text-xs text-slate-400">{file.size} · {file.date}</span>
                </div>
              </div>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                  <Eye size={14} />
                </button>
                <button
                  onClick={() => removeFile(file.name)}
                  className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-10 text-slate-400 text-sm">No documents yet.</div>
      )}
    </div>
  );
}

function ImportDataTab() {
  const sources = [
    { name: 'Apple Health', icon: <Heart size={20} className="text-red-500" />, desc: 'Import activity, heart rate & sleep data' },
    { name: 'Google Fit', icon: <Activity size={20} className="text-blue-500" />, desc: 'Sync fitness and wellness metrics' },
    { name: 'Fitbit', icon: <Dumbbell size={20} className="text-teal-500" />, desc: 'Steps, calories, and workout history' },
    { name: 'MyFitnessPal', icon: <Apple size={20} className="text-green-500" />, desc: 'Nutrition and dietary tracking' },
    { name: 'Withings', icon: <Brain size={20} className="text-purple-500" />, desc: 'Weight, blood pressure & ECG data' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-slate-900 mb-1">Connect Health Apps</h2>
        <p className="text-sm text-slate-500">Sync data from your fitness and health trackers to enrich your case insights.</p>
      </div>
      <div className="space-y-2.5">
        {sources.map((s) => (
          <div
            key={s.name}
            className="flex items-center gap-4 px-4 py-3.5 bg-white rounded-xl border border-slate-200 hover:border-slate-300 transition-all"
          >
            <div className="w-9 h-9 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center flex-shrink-0">
              {s.icon}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-800">{s.name}</p>
              <p className="text-xs text-slate-400">{s.desc}</p>
            </div>
            <button className="px-3.5 py-1.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
              Connect
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main page ─────────────────────────────────────────────────────────────

export default function CaseDashboard() {
  const params = useParams();
  const searchParams = useSearchParams();

  const caseId = params.id as string;
  const activeTab = (searchParams.get('tab') ?? 'analytics') as TabId;

  // Try mock data first; if not found, fetch from backend
  const mockCase = mockCases.find((c) => c.id === caseId);
  const [caseData, setCaseData] = useState(mockCase ?? mockCases[0]);
  const [caseLoaded, setCaseLoaded] = useState(!!mockCase);

  useEffect(() => {
    if (mockCase) return; // already have the data
    getCase(caseId)
      .then((data) => { setCaseData(data); setCaseLoaded(true); })
      .catch(() => setCaseLoaded(true)); // fallback stays as mockCases[0]
  }, [caseId]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="p-8 max-w-5xl">
      {/* Page title */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">
          {caseLoaded ? caseData.title : <span className="inline-block w-64 h-7 bg-slate-100 rounded animate-pulse" />}
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          {caseLoaded
            ? `${caseData.doctorName} · ${new Date(caseData.visitDate).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}`
            : <span className="inline-block w-48 h-4 bg-slate-100 rounded animate-pulse" />}
        </p>
      </div>

      {/* Tab content */}
      {activeTab === 'analytics' && <AnalyticsTab specialty={caseData.specialty} />}
      {activeTab === 'videos' && <VideosTab caseId={caseId} />}
      {activeTab === 'calendar' && <CalendarTab />}
      {activeTab === 'articles' && <ArticlesTab specialty={caseData.specialty} />}
      {activeTab === 'game' && <GameTab />}
      {activeTab === 'documents' && <DocumentsTab />}
      {activeTab === 'import' && <ImportDataTab />}
    </div>
  );
}
