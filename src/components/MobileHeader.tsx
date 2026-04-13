'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useState } from 'react';
import { Bell, Sparkles } from 'lucide-react';
import AIAssistant from './AIAssistant';

export default function MobileHeader() {
  const [chatOpen, setChatOpen] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-40 px-5 pt-4 pb-3 bg-hippo-bg/80 backdrop-blur-lg">
        <div className="flex items-center justify-between">
          {/* Logo + wordmark */}
          <Link href="/" className="flex items-center gap-2.5">
            <div className="relative w-11 h-11 rounded-full overflow-hidden ring-2 ring-hippo-pink-hot shadow-[0_4px_14px_-2px_rgba(244,140,186,0.5)]">
              <Image src="/logo.jpeg" alt="Hippo" fill sizes="44px" className="object-cover" />
            </div>
            <span className="text-[22px] font-extrabold tracking-tight text-hippo-ink leading-none">
              Hippo
            </span>
          </Link>

          {/* Right actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setChatOpen(true)}
              aria-label="Open Hippo chat"
              className="relative w-11 h-11 rounded-full bg-white flex items-center justify-center shadow-[0_4px_14px_-2px_rgba(244,140,186,0.35)] active:scale-95 transition-transform"
            >
              <Sparkles size={18} className="text-hippo-pink-hot" strokeWidth={2.5} />
            </button>

            <Link
              href="/cases"
              aria-label="Notifications"
              className="relative w-11 h-11 rounded-full bg-white flex items-center justify-center shadow-[0_4px_14px_-2px_rgba(244,140,186,0.35)] active:scale-95 transition-transform"
            >
              <Bell size={18} className="text-hippo-ink" strokeWidth={2.5} />
              <span className="absolute top-2 right-2.5 w-2 h-2 rounded-full bg-hippo-pink-hot ring-2 ring-white" />
              <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-hippo-pink-hot text-white text-[10px] font-bold flex items-center justify-center">
                4
              </span>
            </Link>

            <Link
              href="/settings"
              aria-label="Your profile"
              className="w-11 h-11 rounded-full overflow-hidden ring-2 ring-white shadow-[0_4px_14px_-2px_rgba(244,140,186,0.35)]"
            >
              <div className="w-full h-full bg-gradient-to-br from-hippo-pink to-hippo-pink-hot flex items-center justify-center text-white font-bold text-sm">
                E
              </div>
            </Link>
          </div>
        </div>
      </header>

      <AIAssistant open={chatOpen} onClose={() => setChatOpen(false)} />
    </>
  );
}
