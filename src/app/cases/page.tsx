'use client';

import { useState } from 'react';
import { Plus, Search, FolderOpen } from 'lucide-react';
import CaseCard from '@/components/CaseCard';
import CreateCaseModal from '@/components/CreateCaseModal';
import { mockCases } from '@/lib/mockData';
import { MedicalCase } from '@/types';

export default function CasesPage() {
  const [cases, setCases] = useState<MedicalCase[]>(mockCases);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [search, setSearch] = useState('');

  const handleCreate = (newCase: MedicalCase) => {
    setCases((prev) => [newCase, ...prev]);
    setIsModalOpen(false);
  };

  const filtered = cases.filter((c) =>
    !search ||
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    c.doctorName.toLowerCase().includes(search.toLowerCase()) ||
    c.specialty.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Page header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">My Consultations</h1>
          <p className="text-slate-500 mt-1">
            {cases.length} consultation{cases.length !== 1 ? 's' : ''} recorded
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2.5 px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-xl hover:bg-blue-700 active:scale-95 transition-all shadow-sm shadow-blue-200"
        >
          <Plus size={18} />
          New Case
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-sm">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by title, doctor or specialty..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
          />
        </div>
      </div>

      {/* Cases grid */}
      {filtered.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filtered.map((c) => (
            <CaseCard key={c.id} medicalCase={c} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
            <FolderOpen size={28} className="text-slate-300" />
          </div>
          <h3 className="text-base font-semibold text-slate-700 mb-1">No cases found</h3>
          <p className="text-sm text-slate-400 max-w-xs">
            {search
              ? 'Try adjusting your search.'
              : 'Create your first case to start tracking your health journey.'}
          </p>
          {!search && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="mt-5 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus size={15} />
              Create First Case
            </button>
          )}
        </div>
      )}

      {isModalOpen && (
        <CreateCaseModal onClose={() => setIsModalOpen(false)} onCreate={handleCreate} />
      )}
    </div>
  );
}
