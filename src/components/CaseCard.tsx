'use client';

import { MedicalCase } from '@/types';
import { Calendar, FileText, Mic, ChevronRight } from 'lucide-react';
import Link from 'next/link';

const specialtyEmoji: Record<string, string> = {
  Cardiology: '🫀',
  Orthopedics: '🦴',
  Endocrinology: '🩸',
  Neurology: '🧠',
  Dermatology: '🧴',
  Pediatrics: '🧸',
  Pulmonology: '🫁',
  Oncology: '🎗️',
  default: '🩺',
};

interface CaseCardProps {
  medicalCase: MedicalCase;
}

export default function CaseCard({ medicalCase }: CaseCardProps) {
  const emoji = specialtyEmoji[medicalCase.specialty] ?? specialtyEmoji.default;
  const visitDate = new Date(medicalCase.visitDate).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <Link href={`/cases/${medicalCase.id}`} className="block">
      <div className="bg-white rounded-[24px] p-5 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)] active:scale-[0.99] transition-transform">
        <div className="flex items-start gap-3">
          {/* Specialty avatar */}
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-hippo-pink-soft to-hippo-pink flex items-center justify-center text-2xl flex-shrink-0 shadow-[0_4px_12px_-4px_rgba(244,140,186,0.5)]">
            {emoji}
          </div>

          <div className="flex-1 min-w-0">
            <span className="inline-block text-[10px] font-bold text-hippo-pink-hot bg-hippo-pink-soft px-2 py-0.5 rounded-full uppercase tracking-wide">
              {medicalCase.specialty}
            </span>
            <h3 className="font-extrabold text-hippo-ink text-[15px] leading-tight mt-1.5">
              {medicalCase.title}
            </h3>
            <p className="text-[11px] text-hippo-ink-soft mt-0.5">{medicalCase.doctorName}</p>
          </div>

          <ChevronRight size={18} className="text-hippo-pink-hot flex-shrink-0 mt-2" />
        </div>

        <p className="text-[12px] text-hippo-ink-soft line-clamp-2 mt-3 leading-relaxed">
          {medicalCase.summary}
        </p>

        {medicalCase.symptoms.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {medicalCase.symptoms.slice(0, 3).map((symptom) => (
              <span
                key={symptom}
                className="text-[10px] font-medium bg-hippo-pink-soft/60 text-hippo-ink px-2.5 py-1 rounded-full"
              >
                {symptom}
              </span>
            ))}
          </div>
        )}

        <div className="flex items-center gap-4 mt-4 pt-3 border-t border-hippo-pink-soft text-[10px] text-hippo-ink-soft font-medium">
          <span className="flex items-center gap-1">
            <Calendar size={11} />
            {visitDate}
          </span>
          {medicalCase.documentsCount > 0 && (
            <span className="flex items-center gap-1">
              <FileText size={11} />
              {medicalCase.documentsCount} doc{medicalCase.documentsCount !== 1 ? 's' : ''}
            </span>
          )}
          {medicalCase.hasVoiceNote && (
            <span className="flex items-center gap-1 text-hippo-pink-hot">
              <Mic size={11} />
              Voice
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
