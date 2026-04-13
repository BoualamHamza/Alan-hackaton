'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Search, FolderOpen, Plus } from 'lucide-react';
import CaseCard from '@/components/CaseCard';
import { mockCases } from '@/lib/mockData';
import { MedicalCase } from '@/types';

export default function CasesPage() {
  const [cases] = useState<MedicalCase[]>(mockCases);
  const [search, setSearch] = useState('');

  const filtered = cases.filter((c) =>
    !search ||
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    c.doctorName.toLowerCase().includes(search.toLowerCase()) ||
    c.specialty.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <header className="px-1">
        <h1 className="text-[22px] font-extrabold text-hippo-ink leading-tight">My Consultations</h1>
        <p className="text-[12px] text-hippo-ink-soft mt-0.5">
          {cases.length} consultation{cases.length !== 1 ? 's' : ''} recorded
        </p>
      </header>

      <div className="relative">
        <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-hippo-ink-soft" />
        <input
          type="text"
          placeholder="Search by title, doctor or specialty…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-11 pr-4 py-3.5 bg-white rounded-full text-sm text-hippo-ink placeholder:text-hippo-ink-soft focus:outline-none focus:ring-2 focus:ring-hippo-pink-hot shadow-[0_4px_20px_-10px_rgba(244,140,186,0.4)]"
        />
      </div>

      {filtered.length > 0 ? (
        <div className="space-y-3">
          {filtered.map((c) => (
            <CaseCard key={c.id} medicalCase={c} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center text-center py-14 bg-white rounded-[24px] shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)]">
          <div className="w-16 h-16 rounded-3xl bg-hippo-pink-soft flex items-center justify-center mb-4">
            <FolderOpen size={28} className="text-hippo-pink-hot" />
          </div>
          <h3 className="text-sm font-bold text-hippo-ink mb-1">No cases found</h3>
          <p className="text-xs text-hippo-ink-soft max-w-xs px-4">
            {search
              ? 'Try adjusting your search.'
              : 'Tap the + button to create your first case.'}
          </p>
          {!search && (
            <Link
              href="?new=1"
              className="mt-5 flex items-center gap-2 px-5 py-3 bg-hippo-pink-hot text-white text-sm font-bold rounded-full shadow-[0_8px_20px_-6px_rgba(244,140,186,0.8)] active:scale-95 transition-transform"
            >
              <Plus size={16} strokeWidth={3} />
              Create first case
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
