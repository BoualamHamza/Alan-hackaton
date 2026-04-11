'use client';

import { MedicalCase } from '@/types';
import { Calendar, FileText, Mic, ChevronRight } from 'lucide-react';
import Link from 'next/link';

const specialtyColors: Record<string, string> = {
  Cardiology: 'bg-red-100 text-red-700',
  Orthopedics: 'bg-blue-100 text-blue-700',
  Endocrinology: 'bg-purple-100 text-purple-700',
  Neurology: 'bg-indigo-100 text-indigo-700',
  default: 'bg-teal-100 text-teal-700',
};

interface CaseCardProps {
  medicalCase: MedicalCase;
}

export default function CaseCard({ medicalCase }: CaseCardProps) {
  const specialtyColor = specialtyColors[medicalCase.specialty] || specialtyColors.default;
  const visitDate = new Date(medicalCase.visitDate).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <Link href={`/cases/${medicalCase.id}`}>
      <div className="bg-white rounded-xl border border-slate-200 p-5 hover:border-blue-300 hover:shadow-md transition-all duration-200 cursor-pointer group">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            {/* Specialty badge */}
            <div className="mb-2">
              <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${specialtyColor}`}>
                {medicalCase.specialty}
              </span>
            </div>

            <h3 className="font-semibold text-slate-900 text-base leading-snug group-hover:text-blue-700 transition-colors mb-1">
              {medicalCase.title}
            </h3>
            <p className="text-sm text-slate-500 mb-3">{medicalCase.doctorName}</p>

            {/* Summary */}
            <p className="text-sm text-slate-600 line-clamp-2 mb-4 leading-relaxed">
              {medicalCase.summary}
            </p>

            {/* Symptoms */}
            <div className="flex flex-wrap gap-1.5 mb-4">
              {medicalCase.symptoms.slice(0, 3).map((symptom) => (
                <span
                  key={symptom}
                  className="text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full"
                >
                  {symptom}
                </span>
              ))}
            </div>

            {/* Footer */}
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <span className="flex items-center gap-1.5">
                <Calendar size={12} />
                {visitDate}
              </span>
              {medicalCase.documentsCount > 0 && (
                <span className="flex items-center gap-1.5">
                  <FileText size={12} />
                  {medicalCase.documentsCount} doc{medicalCase.documentsCount !== 1 ? 's' : ''}
                </span>
              )}
              {medicalCase.hasVoiceNote && (
                <span className="flex items-center gap-1.5 text-blue-400">
                  <Mic size={12} />
                  Voice note
                </span>
              )}
            </div>
          </div>

          {/* Arrow */}
          <div className="mt-1 p-1.5 rounded-lg text-slate-300 group-hover:text-blue-500 group-hover:bg-blue-50 transition-all">
            <ChevronRight size={16} />
          </div>
        </div>
      </div>
    </Link>
  );
}
