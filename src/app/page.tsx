'use client';

import Link from 'next/link';
import { useState } from 'react';
import {
  Zap, Moon, Tag, Home as HomeIcon, Film, Gamepad2, Play,
  Heart, Activity, Clock, ChevronRight, MessageCircle,
} from 'lucide-react';

const MOODS = [
  { emoji: '😄', label: 'Great', value: 'great' },
  { emoji: '🙂', label: 'Good', value: 'good' },
  { emoji: '😐', label: 'Okay', value: 'okay' },
  { emoji: '😔', label: 'Low', value: 'low' },
] as const;

const HOME_TABS = [
  { id: 'home', label: 'Home', icon: HomeIcon },
  { id: 'reels', label: 'Reels', icon: Film },
  { id: 'games', label: 'Games', icon: Gamepad2 },
] as const;

export default function HomePage() {
  const [mood, setMood] = useState<string>('good');
  const [sleep, setSleep] = useState<string>('7 hrs');
  const [submitted, setSubmitted] = useState(false);
  const [activeChip, setActiveChip] = useState<string>('home');

  const handleSubmit = () => {
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 2000);
  };

  return (
    <div className="space-y-5">
      {/* ─── Greeting + mood card ─── */}
      <section className="bg-white rounded-[28px] p-5 shadow-[0_8px_30px_-12px_rgba(244,140,186,0.4)]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-[22px] font-extrabold text-hippo-ink leading-tight">
              Good Morning, Emma!
            </h1>
            <p className="text-[13px] text-hippo-ink-soft mt-1">
              How are you feeling today?
            </p>
          </div>
          <div className="flex gap-1.5">
            {MOODS.map((m) => (
              <button
                key={m.value}
                onClick={() => setMood(m.value)}
                className={`w-9 h-9 rounded-full flex items-center justify-center text-lg transition-all ${
                  mood === m.value
                    ? 'bg-hippo-pink scale-110 shadow-[0_4px_12px_-4px_rgba(244,140,186,0.8)]'
                    : 'bg-hippo-pink-soft'
                }`}
                aria-label={m.label}
              >
                {m.emoji}
              </button>
            ))}
          </div>
        </div>

        {/* Quick-log tiles */}
        <div className="mt-5 grid grid-cols-3 gap-2.5">
          <QuickTile icon={Zap} label="Energy" value="High" accent="amber" />
          <QuickTile
            icon={Moon}
            label="Sleep"
            value={sleep}
            accent="indigo"
            onClick={() => setSleep(sleep === '7 hrs' ? '8 hrs' : '7 hrs')}
          />
          <QuickTile icon={Tag} label="Symptoms" value="Mild" accent="pink" />
        </div>

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          className="w-full mt-5 py-4 bg-hippo-pink-hot text-white rounded-full font-bold text-[15px] shadow-[0_10px_30px_-8px_rgba(244,140,186,0.8)] active:scale-[0.98] transition-transform"
        >
          {submitted ? '✓ Logged for today' : 'Submit'}
        </button>
      </section>

      {/* ─── Tab chips ─── */}
      <section>
        <div className="flex gap-2 bg-white rounded-full p-1.5 shadow-[0_4px_20px_-10px_rgba(244,140,186,0.4)]">
          {HOME_TABS.map(({ id, label, icon: Icon }) => {
            const active = activeChip === id;
            return (
              <button
                key={id}
                onClick={() => setActiveChip(id)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-full text-xs font-bold transition-all ${
                  active ? 'bg-hippo-ink text-white' : 'text-hippo-ink-soft'
                }`}
              >
                <Icon size={14} strokeWidth={2.5} />
                {label}
              </button>
            );
          })}
        </div>
      </section>

      {/* ─── Featured article + reels rail ─── */}
      <section className="grid grid-cols-[1fr_92px] gap-3">
        {/* Article card */}
        <Link
          href="/cases/2"
          className="bg-white rounded-[24px] overflow-hidden shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)] active:scale-[0.99] transition-transform"
        >
          <div className="h-32 bg-gradient-to-br from-hippo-pink-soft to-hippo-pink relative">
            <div className="absolute inset-0 flex items-end p-3">
              <div className="w-14 h-14 rounded-full bg-white ring-2 ring-white shadow-md overflow-hidden flex items-center justify-center text-2xl">
                👨‍⚕️
              </div>
            </div>
            <span className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm px-2 py-1 rounded-full text-[9px] font-bold text-hippo-ink">
              ARTICLE
            </span>
          </div>
          <div className="p-3">
            <h3 className="text-[13px] font-bold text-hippo-ink leading-tight line-clamp-2">
              Managing Cholesterol: What You Should Know
            </h3>
            <div className="flex items-center gap-2 mt-2 text-[10px] text-hippo-ink-soft">
              <span>Today</span>
              <span>•</span>
              <span>Cholesterol, Heart Health</span>
            </div>
            <div className="flex items-center gap-3 mt-2">
              <span className="flex items-center gap-1 text-[10px] text-hippo-ink-soft">
                <Heart size={11} className="text-hippo-pink-hot" fill="currentColor" /> 17
              </span>
              <span className="flex items-center gap-1 text-[10px] text-hippo-ink-soft">
                <MessageCircle size={11} /> 4
              </span>
            </div>
          </div>
        </Link>

        {/* Reels rail */}
        <Link
          href="/reels"
          className="bg-white rounded-[24px] p-2 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)] flex flex-col gap-2"
        >
          <div className="flex items-center gap-1 text-[10px] font-bold text-hippo-ink mb-0.5 pl-1">
            <Play size={11} className="text-hippo-pink-hot" fill="currentColor" />
            Reels
          </div>
          <div className="relative h-20 rounded-2xl bg-gradient-to-br from-hippo-pink-soft to-hippo-pink overflow-hidden flex items-center justify-center">
            <span className="text-2xl">👩‍⚕️</span>
            <div className="absolute bottom-1 left-1 right-1 text-[8px] font-bold text-white leading-tight drop-shadow text-center">
              Cholesterol Basics
            </div>
          </div>
          <div className="relative h-16 rounded-2xl bg-gradient-to-br from-hippo-pink to-hippo-pink-hot overflow-hidden flex items-center justify-center">
            <span className="text-xl">🫀</span>
          </div>
        </Link>
      </section>

      {/* ─── Metrics mini-cards ─── */}
      <section>
        <div className="flex items-center justify-between mb-2.5">
          <h2 className="text-[13px] font-bold text-hippo-ink">Metrics</h2>
          <Link
            href="/metrics"
            className="text-[11px] font-bold text-hippo-pink-hot flex items-center gap-0.5"
          >
            View all <ChevronRight size={12} />
          </Link>
        </div>
        <div className="grid grid-cols-3 gap-2.5">
          <MetricMini icon={Clock} value="7 hrs" label="Sleep" />
          <MetricMini icon={Activity} value="6,548" label="Steps" />
          <MetricMini icon={Heart} value="76 bpm" label="Heart rate" />
        </div>
      </section>

      {/* ─── Health Quiz card ─── */}
      <section>
        <Link
          href="/games"
          className="block bg-white rounded-[24px] p-4 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)] active:scale-[0.99] transition-transform"
        >
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-hippo-pink to-hippo-pink-hot flex items-center justify-center text-2xl flex-shrink-0 shadow-[0_6px_16px_-4px_rgba(244,140,186,0.6)]">
              🎯
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-[14px] font-bold text-hippo-ink">Health Quiz</h3>
              <p className="text-[11px] text-hippo-ink-soft mt-0.5">Cholesterol challenge</p>
              <div className="flex items-center gap-3 mt-1.5 text-[10px] text-hippo-ink-soft">
                <span className="flex items-center gap-1">
                  <Clock size={10} /> 5 min
                </span>
                <span className="flex items-center gap-1">
                  <Activity size={10} /> 3 questions
                </span>
              </div>
            </div>
            <ChevronRight size={18} className="text-hippo-pink-hot" />
          </div>
        </Link>
      </section>
    </div>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function QuickTile({
  icon: Icon,
  label,
  value,
  accent,
  onClick,
}: {
  icon: React.ComponentType<{ size?: number; className?: string; strokeWidth?: number }>;
  label: string;
  value: string;
  accent: 'amber' | 'indigo' | 'pink';
  onClick?: () => void;
}) {
  const accentClasses = {
    amber: 'bg-amber-100 text-amber-600',
    indigo: 'bg-indigo-100 text-indigo-600',
    pink: 'bg-hippo-pink-soft text-hippo-pink-hot',
  }[accent];

  return (
    <button
      onClick={onClick}
      className="bg-hippo-pink-soft/60 rounded-[18px] p-3 text-left active:scale-95 transition-transform"
    >
      <div className={`w-8 h-8 rounded-xl ${accentClasses} flex items-center justify-center mb-2`}>
        <Icon size={16} strokeWidth={2.5} />
      </div>
      <p className="text-[10px] font-bold text-hippo-ink-soft uppercase tracking-wide">{label}</p>
      <p className="text-[13px] font-bold text-hippo-ink mt-0.5">{value}</p>
    </button>
  );
}

function MetricMini({
  icon: Icon,
  value,
  label,
}: {
  icon: React.ComponentType<{ size?: number; className?: string; strokeWidth?: number }>;
  value: string;
  label: string;
}) {
  return (
    <div className="bg-white rounded-[18px] p-3 shadow-[0_4px_16px_-8px_rgba(244,140,186,0.4)]">
      <div className="w-8 h-8 rounded-xl bg-hippo-pink-soft flex items-center justify-center mb-2">
        <Icon size={15} className="text-hippo-pink-hot" strokeWidth={2.5} />
      </div>
      <p className="text-[14px] font-extrabold text-hippo-ink leading-none">{value}</p>
      <p className="text-[10px] text-hippo-ink-soft mt-1 font-medium">{label}</p>
    </div>
  );
}
