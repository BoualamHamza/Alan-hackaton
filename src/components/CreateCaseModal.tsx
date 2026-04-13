'use client';

import { useState, useRef, useCallback } from 'react';
import { X, Mic, MicOff, Upload, FileText, Trash2, ChevronRight, Check, AlertCircle, Loader2 } from 'lucide-react';
import { specialties } from '@/lib/mockData';
import { MedicalCase } from '@/types';
import { createCase } from '@/lib/api';

interface CreateCaseModalProps {
  onClose: () => void;
  onCreate: (newCase: MedicalCase) => void;
}

type Step = 1 | 2 | 3;

const inputClass =
  'w-full px-4 py-3 bg-hippo-pink-soft/50 rounded-2xl text-sm text-hippo-ink placeholder:text-hippo-ink-soft focus:outline-none focus:ring-2 focus:ring-hippo-pink-hot transition-all';

export default function CreateCaseModal({ onClose, onCreate }: CreateCaseModalProps) {
  const [step, setStep] = useState<Step>(1);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [voiceBlob, setVoiceBlob] = useState<Blob | null>(null);
  const [inputMode, setInputMode] = useState<'text' | 'voice'>('text');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);

  const [form, setForm] = useState({
    title: '',
    specialty: '',
    doctorName: '',
    visitDate: '',
    summary: '',
    symptoms: '',
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const updateField = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  // Voice recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: BlobPart[] = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setVoiceBlob(blob);
        stream.getTracks().forEach((t) => t.stop());
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => setRecordingTime((t) => t + 1), 1000);
    } catch {
      alert('Microphone access denied. Please allow microphone permissions.');
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current = null;
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsRecording(false);
  };

  const formatTime = (s: number) =>
    `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;

  // File handling
  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    const newFiles = Array.from(files).filter(
      (f) => !uploadedFiles.find((existing) => existing.name === f.name)
    );
    setUploadedFiles((prev) => [...prev, ...newFiles]);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uploadedFiles]);

  const removeFile = (name: string) =>
    setUploadedFiles((prev) => prev.filter((f) => f.name !== name));

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setSubmitError(null);

    const fd = new FormData();
    fd.append('title', form.title);
    fd.append('specialty', form.specialty);
    fd.append('doctorName', form.doctorName);
    fd.append('visitDate', form.visitDate);
    fd.append('summary', form.summary);
    fd.append('symptoms', form.symptoms);
    fd.append('hasVoiceNote', voiceBlob ? 'true' : 'false');
    for (const file of uploadedFiles) fd.append('documents', file);
    if (voiceBlob) fd.append('voiceNote', voiceBlob, 'voice_note.webm');

    try {
      const newCase = await createCase(fd);
      onCreate(newCase);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
      setIsSubmitting(false);
    }
  };

  const isStep1Valid = !!(form.title && form.specialty && form.doctorName && form.visitDate);
  const isStep2Valid = !!(form.summary || voiceBlob);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div
        className="relative w-full max-w-md h-[92vh] bg-white rounded-t-[32px] flex flex-col overflow-hidden animate-[slideUp_0.3s_ease-out]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-5 pb-4">
          <div>
            <h2 className="text-[18px] font-extrabold text-hippo-ink leading-tight">New case</h2>
            <p className="text-[11px] text-hippo-ink-soft mt-0.5">
              Step {step} of 3 · {['Consultation info', 'Your notes', 'Documents'][step - 1]}
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center bg-hippo-pink-soft rounded-full active:scale-95 transition-transform"
            aria-label="Close"
          >
            <X size={18} className="text-hippo-ink" strokeWidth={2.5} />
          </button>
        </div>

        {/* Progress bar */}
        <div className="px-5 mb-2">
          <div className="flex gap-1.5">
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                className={`flex-1 h-1.5 rounded-full transition-all ${
                  n <= step ? 'bg-hippo-pink-hot' : 'bg-hippo-pink-soft'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {step === 1 && (
            <div className="space-y-4">
              <Field label="Case title" required>
                <input
                  type="text"
                  placeholder="e.g., Lower Back Pain Follow-up"
                  value={form.title}
                  onChange={(e) => updateField('title', e.target.value)}
                  className={inputClass}
                />
              </Field>

              <Field label="Medical specialty" required>
                <select
                  value={form.specialty}
                  onChange={(e) => updateField('specialty', e.target.value)}
                  className={inputClass}
                >
                  <option value="">Select specialty…</option>
                  {specialties.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </Field>

              <Field label="Visit date" required>
                <input
                  type="date"
                  value={form.visitDate}
                  max={new Date().toISOString().split('T')[0]}
                  onChange={(e) => updateField('visitDate', e.target.value)}
                  className={inputClass}
                />
              </Field>

              <Field label="Doctor's name" required>
                <input
                  type="text"
                  placeholder="e.g., Dr. Sarah Mitchell"
                  value={form.doctorName}
                  onChange={(e) => updateField('doctorName', e.target.value)}
                  className={inputClass}
                />
              </Field>

              <Field label="Symptoms (comma-separated)">
                <input
                  type="text"
                  placeholder="e.g., Headache, Fatigue, Nausea"
                  value={form.symptoms}
                  onChange={(e) => updateField('symptoms', e.target.value)}
                  className={inputClass}
                />
              </Field>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <p className="text-[12px] text-hippo-ink-soft">
                Capture what you discussed with your doctor and what you understood.
              </p>

              <div className="flex bg-hippo-pink-soft/50 rounded-full p-1">
                <button
                  onClick={() => setInputMode('text')}
                  className={`flex-1 py-2.5 text-xs font-bold rounded-full transition-all ${
                    inputMode === 'text' ? 'bg-white text-hippo-ink shadow-sm' : 'text-hippo-ink-soft'
                  }`}
                >
                  Text notes
                </button>
                <button
                  onClick={() => setInputMode('voice')}
                  className={`flex-1 py-2.5 text-xs font-bold rounded-full transition-all ${
                    inputMode === 'voice' ? 'bg-white text-hippo-ink shadow-sm' : 'text-hippo-ink-soft'
                  }`}
                >
                  Voice note
                </button>
              </div>

              {inputMode === 'text' ? (
                <textarea
                  placeholder="Describe what the doctor told you, what you understood, and any questions you still have…"
                  value={form.summary}
                  onChange={(e) => updateField('summary', e.target.value)}
                  rows={8}
                  className={`${inputClass} resize-none leading-relaxed`}
                />
              ) : (
                <div className="bg-hippo-pink-soft/40 rounded-3xl p-8 flex flex-col items-center gap-4">
                  <button
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`w-20 h-20 rounded-full flex items-center justify-center transition-all shadow-[0_12px_32px_-8px_rgba(244,140,186,0.6)] ${
                      isRecording ? 'bg-red-500 animate-pulse' : 'bg-hippo-pink-hot'
                    }`}
                  >
                    {isRecording ? <MicOff size={28} className="text-white" /> : <Mic size={28} className="text-white" />}
                  </button>

                  {isRecording && (
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                      <span className="text-sm font-mono text-red-500 font-bold">
                        {formatTime(recordingTime)}
                      </span>
                    </div>
                  )}

                  <p className="text-xs text-hippo-ink-soft text-center">
                    {isRecording
                      ? 'Recording… tap to stop'
                      : voiceBlob
                        ? 'Recording saved — tap to re-record'
                        : 'Tap to start recording'}
                  </p>

                  {voiceBlob && !isRecording && (
                    <div className="flex items-center gap-2 px-4 py-2.5 bg-white rounded-full shadow-sm">
                      <Check size={14} className="text-hippo-pink-hot" strokeWidth={3} />
                      <span className="text-xs text-hippo-ink font-bold">
                        Voice note recorded ({formatTime(recordingTime)})
                      </span>
                    </div>
                  )}
                </div>
              )}

              {!form.summary && !voiceBlob && (
                <div className="flex items-start gap-2 px-4 py-3 bg-amber-50 rounded-2xl">
                  <AlertCircle size={14} className="text-amber-500 mt-0.5 flex-shrink-0" />
                  <p className="text-[11px] text-amber-700">
                    Add text notes or a voice recording to continue.
                  </p>
                </div>
              )}
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <p className="text-[12px] text-hippo-ink-soft">
                Upload any documents from your consultation — prescriptions, lab results, imaging reports.
              </p>

              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={onDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`rounded-3xl p-7 flex flex-col items-center gap-3 cursor-pointer transition-all ${
                  isDragOver
                    ? 'bg-hippo-pink-soft ring-2 ring-hippo-pink-hot'
                    : 'bg-hippo-pink-soft/40'
                }`}
              >
                <div className="w-14 h-14 rounded-2xl bg-white flex items-center justify-center shadow-[0_4px_14px_-4px_rgba(244,140,186,0.4)]">
                  <Upload size={22} className="text-hippo-pink-hot" strokeWidth={2.5} />
                </div>
                <div className="text-center">
                  <p className="text-[13px] font-bold text-hippo-ink">Drop files here or tap to browse</p>
                  <p className="text-[11px] text-hippo-ink-soft mt-0.5">PDF, JPG, PNG, DOCX — up to 10 MB</p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.jpg,.jpeg,.png,.docx,.doc"
                  className="hidden"
                  onChange={(e) => handleFiles(e.target.files)}
                />
              </div>

              {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                  <p className="text-[10px] font-bold text-hippo-ink-soft uppercase tracking-wide">
                    Uploaded ({uploadedFiles.length})
                  </p>
                  {uploadedFiles.map((file) => (
                    <div
                      key={file.name}
                      className="flex items-center gap-3 px-4 py-3 bg-hippo-pink-soft/50 rounded-2xl"
                    >
                      <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center flex-shrink-0">
                        <FileText size={14} className="text-hippo-pink-hot" strokeWidth={2.5} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[12px] font-bold text-hippo-ink truncate">{file.name}</p>
                        <p className="text-[10px] text-hippo-ink-soft">{formatFileSize(file.size)}</p>
                      </div>
                      <button
                        onClick={() => removeFile(file.name)}
                        className="p-2 text-hippo-ink-soft active:text-red-500"
                        aria-label="Remove"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {uploadedFiles.length === 0 && (
                <p className="text-[11px] text-center text-hippo-ink-soft py-2">
                  Documents are optional — you can add them later.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-4 bg-white border-t border-hippo-pink-soft space-y-3">
          {submitError && (
            <div className="flex items-start gap-2 px-3 py-2.5 bg-red-50 rounded-2xl">
              <AlertCircle size={14} className="text-red-500 mt-0.5 flex-shrink-0" />
              <p className="text-[11px] text-red-700">{submitError}</p>
            </div>
          )}
          <div className="flex items-center justify-between gap-3">
            <button
              onClick={() => (step > 1 ? setStep((s) => (s - 1) as Step) : onClose())}
              disabled={isSubmitting}
              className="px-5 py-3 text-xs font-bold text-hippo-ink-soft active:bg-hippo-pink-soft rounded-full transition-colors disabled:opacity-40"
            >
              {step === 1 ? 'Cancel' : 'Back'}
            </button>

            {step < 3 ? (
              <button
                onClick={() => setStep((s) => (s + 1) as Step)}
                disabled={step === 1 ? !isStep1Valid : !isStep2Valid}
                className="flex items-center gap-1.5 px-6 py-3 bg-hippo-pink-hot text-white text-xs font-bold rounded-full shadow-[0_8px_20px_-6px_rgba(244,140,186,0.8)] disabled:opacity-40 active:scale-95 transition-all"
              >
                Continue
                <ChevronRight size={14} strokeWidth={3} />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="flex items-center gap-1.5 px-6 py-3 bg-hippo-pink-hot text-white text-xs font-bold rounded-full shadow-[0_8px_20px_-6px_rgba(244,140,186,0.8)] disabled:opacity-60 active:scale-95 transition-all"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={14} className="animate-spin" strokeWidth={3} />
                    Creating…
                  </>
                ) : (
                  <>
                    <Check size={14} strokeWidth={3} />
                    Create case
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-[11px] font-bold text-hippo-ink mb-1.5 px-1">
        {label}
        {required && <span className="text-hippo-pink-hot"> *</span>}
      </label>
      {children}
    </div>
  );
}
