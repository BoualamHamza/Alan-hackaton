'use client';

import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Home, Film, Gamepad2, Activity, Plus } from 'lucide-react';

const tabs = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/reels', label: 'Reels', icon: Film },
  { href: '/games', label: 'Games', icon: Gamepad2 },
  { href: '/metrics', label: 'Metrics', icon: Activity },
] as const;

export default function BottomNav() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  const openCreate = () => {
    const params = new URLSearchParams(searchParams);
    params.set('new', '1');
    router.push(`${pathname}?${params.toString()}`);
  };

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname.startsWith(href);

  // Split: first 2 tabs, then FAB, then last 2 tabs
  const left = tabs.slice(0, 2);
  const right = tabs.slice(2);

  return (
    <nav className="fixed bottom-4 left-1/2 -translate-x-1/2 w-[calc(100%-2rem)] max-w-md z-40">
      <div className="relative bg-white rounded-[32px] shadow-[0_10px_40px_-10px_rgba(244,140,186,0.5)] px-3 py-3 flex items-center justify-between">
        {left.map(({ href, label, icon: Icon }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex flex-col items-center gap-0.5 flex-1 py-1 rounded-2xl transition-all ${
                active ? 'text-hippo-pink-hot' : 'text-hippo-ink-soft'
              }`}
            >
              <Icon size={22} strokeWidth={2.5} />
              <span className="text-[10px] font-bold">{label}</span>
            </Link>
          );
        })}

        {/* Center FAB */}
        <div className="flex-1 flex justify-center">
          <button
            onClick={openCreate}
            aria-label="New case"
            className="w-14 h-14 -mt-7 rounded-full bg-hippo-pink-hot text-white shadow-[0_10px_30px_-4px_rgba(244,140,186,0.8)] flex items-center justify-center active:scale-95 transition-transform ring-4 ring-white"
          >
            <Plus size={26} strokeWidth={3} />
          </button>
        </div>

        {right.map(({ href, label, icon: Icon }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex flex-col items-center gap-0.5 flex-1 py-1 rounded-2xl transition-all ${
                active ? 'text-hippo-pink-hot' : 'text-hippo-ink-soft'
              }`}
            >
              <Icon size={22} strokeWidth={2.5} />
              <span className="text-[10px] font-bold">{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
