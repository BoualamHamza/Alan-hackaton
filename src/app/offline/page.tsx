import Link from 'next/link';
import { WifiOff, RefreshCw } from 'lucide-react';

export const metadata = {
  title: 'Offline — Hippo',
};

export default function OfflinePage() {
  return (
    <div className="flex flex-col items-center justify-center text-center py-20 px-4">
      <div className="w-20 h-20 rounded-3xl bg-hippo-pink-soft flex items-center justify-center mb-5 shadow-[0_12px_32px_-10px_rgba(244,140,186,0.5)]">
        <WifiOff size={32} className="text-hippo-pink-hot" strokeWidth={2.5} />
      </div>

      <h1 className="text-[22px] font-extrabold text-hippo-ink leading-tight">
        You&apos;re offline
      </h1>
      <p className="text-[13px] text-hippo-ink-soft mt-2 max-w-xs">
        Hippo needs a connection to load fresh content. Reconnect and try again —
        your saved cases are still here.
      </p>

      <Link
        href="/"
        className="mt-6 inline-flex items-center gap-2 px-6 py-3 bg-hippo-pink-hot text-white text-[13px] font-bold rounded-full shadow-[0_10px_24px_-6px_rgba(244,140,186,0.8)] active:scale-95 transition-transform"
      >
        <RefreshCw size={14} strokeWidth={3} />
        Retry
      </Link>
    </div>
  );
}
