'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useState, useEffect } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import {
  LayoutDashboard, FolderOpen, Settings,
  Activity, Play, BookOpen, Gamepad2,
  ArrowLeft, Paperclip, Bell, LogOut,
} from 'lucide-react';
import { mockCases } from '@/lib/mockData';
import { getCase } from '@/lib/api';
import { MedicalCase } from '@/types';

const mainNav = [
  { label: 'Cases', href: '/cases', icon: FolderOpen },
  { label: 'Overview', href: '/overview', icon: LayoutDashboard },
  { label: 'Settings', href: '/settings', icon: Settings },
];

const caseTabs = [
  { id: 'analytics', label: 'Analytics', icon: Activity },
  { id: 'videos', label: 'Videos', icon: Play },
  { id: 'articles', label: 'Articles', icon: BookOpen },
  { id: 'game', label: 'Game', icon: Gamepad2 },
  { id: 'documents', label: 'Documents', icon: Paperclip },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  // Detect case detail page: /cases/[id]
  const caseMatch = pathname.match(/^\/cases\/([^/]+)$/);
  const caseId = caseMatch?.[1] ?? null;
  const mockCase = caseId ? mockCases.find((c) => c.id === caseId) ?? null : null;
  const [caseData, setCaseData] = useState<MedicalCase | null>(mockCase);
  const activeTab = searchParams.get('tab') ?? 'analytics';

  useEffect(() => {
    if (!caseId || mockCase) return; // already have mock data
    getCase(caseId).then(setCaseData).catch(() => null);
  }, [caseId]); // eslint-disable-line react-hooks/exhaustive-deps

  const setTab = (tab: string) => {
    router.push(`/cases/${caseId}?tab=${tab}`);
  };

  return (
    <aside className="fixed left-0 top-0 h-screen w-56 bg-white border-r border-slate-100 flex flex-col z-50 shadow-[1px_0_0_0_#f1f5f9]">

      {/* ── Logo ── */}
      <div className="px-5 h-14 flex items-center border-b border-slate-100 flex-shrink-0">
        <Link href="/cases" className="flex items-center gap-2">
          <Image src="/logo.jpeg" alt="Hippo" width={32} height={32} className="rounded-full flex-shrink-0" />
          <span className="text-sm font-bold text-slate-900 tracking-tight">Hippo</span>
        </Link>
      </div>

      {/* ── Navigation area ── */}
      <div className="flex-1 overflow-y-auto">

        {caseData ? (
          /* ── CASE CONTEXT: case info + section tabs ── */
          <div className="flex flex-col h-full">
            {/* Back link */}
            <div className="px-4 pt-4 pb-2">
              <button
                onClick={() => router.push('/cases')}
                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-700 transition-colors group"
              >
                <ArrowLeft size={12} className="group-hover:-translate-x-0.5 transition-transform" />
                All Cases
              </button>
            </div>

            {/* Case identity card */}
            <div className="mx-3 mb-4 p-3 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
                {caseData.specialty}
              </span>
              <p className="text-xs font-semibold text-slate-800 mt-2 leading-snug line-clamp-2">
                {caseData.title}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                {caseData.doctorName}
              </p>
              <p className="text-[11px] text-slate-400">
                {new Date(caseData.visitDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </p>
            </div>

            {/* Section tabs */}
            <div className="px-3">
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2 mb-1.5">
                Sections
              </p>
              <nav className="space-y-0.5">
                {caseTabs.map(({ id, label, icon: Icon }) => {
                  const active = activeTab === id;
                  return (
                    <button
                      key={id}
                      onClick={() => setTab(id)}
                      className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium transition-all text-left ${
                        active
                          ? 'bg-blue-600 text-white'
                          : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
                      }`}
                    >
                      <Icon size={14} className={active ? 'text-white' : 'text-slate-400'} />
                      {label}
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Symptoms pills at bottom of nav area */}
            {caseData.symptoms.length > 0 && (
              <div className="px-4 mt-5">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Symptoms
                </p>
                <div className="flex flex-wrap gap-1">
                  {caseData.symptoms.map((s) => (
                    <span key={s} className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

        ) : (
          /* ── MAIN NAV ── */
          <nav className="px-3 pt-4 space-y-0.5">
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2 mb-2">
              Menu
            </p>
            {mainNav.map(({ label, href, icon: Icon }) => {
              const active = pathname.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-2.5 px-2.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    active
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <Icon size={16} className={active ? 'text-white' : 'text-slate-400'} />
                  {label}
                </Link>
              );
            })}
          </nav>
        )}
      </div>

      {/* ── Footer: notifications + user ── */}
      <div className="flex-shrink-0 border-t border-slate-100 p-3 space-y-0.5">
        <button className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs text-slate-500 hover:text-slate-900 hover:bg-slate-50 transition-colors">
          <span className="relative">
            <Bell size={15} className="text-slate-400" />
            <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-red-500 rounded-full border border-white" />
          </span>
          Notifications
        </button>

        <div className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer group">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0 text-white text-xs font-bold">
            J
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-slate-800 leading-none">John Doe</p>
            <p className="text-[10px] text-slate-400 mt-0.5">Patient</p>
          </div>
          <LogOut size={12} className="text-slate-300 group-hover:text-slate-500 transition-colors flex-shrink-0" />
        </div>
      </div>
    </aside>
  );
}
