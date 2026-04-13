'use client';

import { Gamepad2 } from 'lucide-react';
import QuizGame from '@/components/QuizGame';

export default function GamesPage() {
  return (
    <div className="space-y-5">
      <header className="flex items-center gap-3 px-1">
        <div className="w-12 h-12 rounded-2xl bg-hippo-pink-hot flex items-center justify-center shadow-[0_8px_20px_-6px_rgba(244,140,186,0.6)]">
          <Gamepad2 size={22} className="text-white" strokeWidth={2.5} />
        </div>
        <div>
          <h1 className="text-[22px] font-extrabold text-hippo-ink leading-tight">Games</h1>
          <p className="text-[12px] text-hippo-ink-soft">Learn while you play</p>
        </div>
      </header>

      <QuizGame />
    </div>
  );
}
