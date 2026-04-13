'use client';

import { Film } from 'lucide-react';
import ReelsFeed from '@/components/ReelsFeed';
import { getActiveCase } from '@/lib/activeCase';

export default function ReelsPage() {
  const active = getActiveCase();

  return (
    <div className="space-y-5">
      <header className="flex items-center gap-3 px-1">
        <div className="w-12 h-12 rounded-2xl bg-hippo-pink-hot flex items-center justify-center shadow-[0_8px_20px_-6px_rgba(244,140,186,0.6)]">
          <Film size={22} className="text-white" strokeWidth={2.5} />
        </div>
        <div>
          <h1 className="text-[22px] font-extrabold text-hippo-ink leading-tight">Reels</h1>
          <p className="text-[12px] text-hippo-ink-soft">Short videos for {active.specialty.toLowerCase()}</p>
        </div>
      </header>

      <ReelsFeed caseId={active.id} />
    </div>
  );
}
