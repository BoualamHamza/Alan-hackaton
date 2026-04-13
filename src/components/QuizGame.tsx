'use client';

import { useState } from 'react';
import { Star, Check, X, RotateCcw } from 'lucide-react';

const questions = [
  {
    q: 'What does "chronic" mean in a medical diagnosis?',
    options: ['Severe and sudden', 'Long-lasting, 3+ months', 'Contagious', 'Only affecting older patients'],
    correct: 1,
    explanation: 'Chronic conditions persist for 3 months or longer, as opposed to acute conditions which are short-term.',
  },
  {
    q: 'What is the purpose of an MRI scan?',
    options: ['Measure blood pressure', 'Create detailed images of soft tissues', 'Test blood sugar', 'Check heart rhythm'],
    correct: 1,
    explanation: 'MRI uses magnetic fields to create detailed images of soft tissues, organs, and bones.',
  },
  {
    q: 'What does "HbA1c" measure?',
    options: ['Blood pressure over time', 'Average blood sugar over 3 months', 'Cholesterol levels', 'Liver function'],
    correct: 1,
    explanation: 'HbA1c reflects your average blood glucose levels over the past 2–3 months.',
  },
];

export default function QuizGame() {
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState<number[]>([]);
  const [selected, setSelected] = useState<{ qIdx: number; aIdx: number } | null>(null);

  const handleAnswer = (qIdx: number, aIdx: number) => {
    if (answered.includes(qIdx)) return;
    setSelected({ qIdx, aIdx });
    if (aIdx === questions[qIdx].correct) setScore((s) => s + 10);
    setTimeout(() => {
      setAnswered((prev) => [...prev, qIdx]);
      setSelected(null);
    }, 1200);
  };

  const reset = () => {
    setScore(0);
    setAnswered([]);
    setSelected(null);
  };

  const progress = (answered.length / questions.length) * 100;
  const done = answered.length === questions.length;

  return (
    <div className="space-y-5">
      {/* Score card */}
      <div className="bg-gradient-to-br from-hippo-pink to-hippo-pink-hot rounded-[28px] p-5 text-white shadow-[0_12px_32px_-10px_rgba(244,140,186,0.6)]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider opacity-80">Health Quiz</p>
            <p className="text-3xl font-extrabold mt-1">{score} pts</p>
          </div>
          <div className="w-14 h-14 rounded-2xl bg-white/25 backdrop-blur-sm flex items-center justify-center">
            <Star size={26} className="text-white" fill="currentColor" />
          </div>
        </div>
        <div className="bg-white/30 rounded-full h-2 overflow-hidden">
          <div
            className="bg-white rounded-full h-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-[11px] opacity-90 mt-2 font-medium">
          {answered.length}/{questions.length} questions answered
        </p>
      </div>

      {/* Questions */}
      <div className="space-y-4">
        {questions.map((q, qIdx) => {
          const isDone = answered.includes(qIdx);
          return (
            <div
              key={qIdx}
              className={`bg-white rounded-[24px] p-5 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)] transition-all ${
                isDone ? 'opacity-80' : ''
              }`}
            >
              <div className="flex items-start gap-2 mb-4">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-hippo-pink-soft text-hippo-pink-hot text-xs font-bold flex items-center justify-center mt-0.5">
                  {qIdx + 1}
                </span>
                <p className="text-[14px] font-bold text-hippo-ink leading-tight flex-1">{q.q}</p>
              </div>
              <div className="space-y-2">
                {q.options.map((opt, aIdx) => {
                  const isSel = selected?.qIdx === qIdx && selected.aIdx === aIdx;
                  const isCorrect = q.correct === aIdx;
                  let className =
                    'flex items-center gap-3 px-4 py-3 rounded-2xl text-[13px] font-medium transition-all text-left w-full ';

                  if (isDone) {
                    className += isCorrect
                      ? 'bg-emerald-50 text-emerald-700 ring-2 ring-emerald-200'
                      : 'bg-hippo-pink-soft/40 text-hippo-ink-soft';
                  } else if (isSel) {
                    className += isCorrect
                      ? 'bg-emerald-50 text-emerald-700 ring-2 ring-emerald-300'
                      : 'bg-red-50 text-red-700 ring-2 ring-red-300';
                  } else {
                    className += 'bg-hippo-pink-soft/40 text-hippo-ink active:scale-[0.98]';
                  }

                  return (
                    <button key={aIdx} type="button" className={className} onClick={() => handleAnswer(qIdx, aIdx)}>
                      <div
                        className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                          isDone && isCorrect
                            ? 'bg-emerald-500 text-white'
                            : isSel && !isCorrect
                              ? 'bg-red-500 text-white'
                              : 'bg-white/80'
                        }`}
                      >
                        {isDone && isCorrect ? (
                          <Check size={12} strokeWidth={3} />
                        ) : isSel && !isCorrect ? (
                          <X size={12} strokeWidth={3} />
                        ) : null}
                      </div>
                      <span>{opt}</span>
                    </button>
                  );
                })}
              </div>
              {isDone && (
                <div className="mt-3 px-3 py-2 bg-hippo-pink-soft/60 rounded-xl text-[11px] text-hippo-ink-soft leading-relaxed">
                  <span className="font-bold text-hippo-ink">Why: </span>
                  {q.explanation}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {done && (
        <div className="bg-white rounded-[28px] p-6 text-center shadow-[0_12px_32px_-10px_rgba(244,140,186,0.5)] ring-2 ring-hippo-pink">
          <div className="text-5xl mb-2">🎉</div>
          <p className="text-[18px] font-extrabold text-hippo-ink mb-1">Quiz complete!</p>
          <p className="text-[13px] text-hippo-ink-soft">
            You scored {score}/{questions.length * 10} points.
          </p>
          <button
            onClick={reset}
            className="mt-4 inline-flex items-center gap-2 px-5 py-3 bg-hippo-pink-hot text-white text-sm font-bold rounded-full shadow-[0_8px_20px_-6px_rgba(244,140,186,0.8)] active:scale-95 transition-transform"
          >
            <RotateCcw size={14} strokeWidth={3} /> Play again
          </button>
        </div>
      )}
    </div>
  );
}
