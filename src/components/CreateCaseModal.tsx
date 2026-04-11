'use client';

import { useState, useRef, useCallback } from 'react';
import { X, Mic, MicOff, Upload, FileText, Trash2, ChevronRight, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { specialties } from '@/lib/mockData';
import { MedicalCase } from '@/types';
import { createCase } from '@/lib/api';

interface CreateCaseModalProps {
  onClose: () => void;
  onCreate: (newCase: MedicalCase) => void;
}

type Step = 1 | 2 | 3;

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

      timerRef.current = setInterval(() => {
        setRecordingTime((t) => t + 1);
      }, 1000);
    } catch {
      alert('Microphone access denied. Please allow microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
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
  }, [uploadedFiles]);

  const removeFile = (name: string) =>
    setUploadedFiles((prev) => prev.filter((f) => f.name !== name));

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Submit — sends multipart form data to the backend
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

    for (const file of uploadedFiles) {
      fd.append('documents', file);
    }
    if (voiceBlob) {
      fd.append('voiceNote', voiceBlob, 'voice_note.webm');
    }

    try {
      const newCase = await createCase(fd);
      onCreate(newCase);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
      setIsSubmitting(false);
    }
  };

  const isStep1Valid = form.title && form.specialty && form.doctorName && form.visitDate;
  const isStep2Valid = form.summary || voiceBlob;

  const steps = [
    { num: 1, label: 'Consultation Info' },
    { num: 2, label: 'Your Notes' },
    { num: 3, label: 'Documents' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">New Health Case</h2>
            <p className="text-sm text-slate-500 mt-0.5">Document your consultation experience</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Step indicators */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-100">
          <div className="flex items-center gap-0">
            {steps.map((s, i) => (
              <div key={s.num} className="flex items-center flex-1">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold transition-all ${
                      step > s.num
                        ? 'bg-blue-600 text-white'
                        : step === s.num
                        ? 'bg-blue-600 text-white ring-4 ring-blue-100'
                        : 'bg-white border-2 border-slate-300 text-slate-400'
                    }`}
                  >
                    {step > s.num ? <CheckCircle2 size={14} /> : s.num}
                  </div>
                  <span
                    className={`text-xs font-medium hidden sm:block ${
                      step >= s.num ? 'text-slate-700' : 'text-slate-400'
                    }`}
                  >
                    {s.label}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-3 rounded ${
                      step > s.num ? 'bg-blue-600' : 'bg-slate-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {/* Step 1: Consultation Info */}
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Case Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g., Lower Back Pain Follow-up"
                  value={form.title}
                  onChange={(e) => updateField('title', e.target.value)}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Medical Specialty <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={form.specialty}
                    onChange={(e) => updateField('specialty', e.target.value)}
                    className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white"
                  >
                    <option value="">Select specialty...</option>
                    {specialties.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Visit Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={form.visitDate}
                    max={new Date().toISOString().split('T')[0]}
                    onChange={(e) => updateField('visitDate', e.target.value)}
                    className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Doctor's Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g., Dr. Sarah Mitchell"
                  value={form.doctorName}
                  onChange={(e) => updateField('doctorName', e.target.value)}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Symptoms (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g., Headache, Fatigue, Nausea"
                  value={form.symptoms}
                  onChange={(e) => updateField('symptoms', e.target.value)}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>
            </div>
          )}

          {/* Step 2: Notes */}
          {step === 2 && (
            <div className="space-y-4">
              <div>
                <p className="text-sm text-slate-600 mb-4">
                  Capture what you discussed with your doctor and what you understood. You can type your notes or record a voice memo.
                </p>

                {/* Mode switcher */}
                <div className="flex rounded-lg border border-slate-200 p-1 bg-slate-50 mb-4">
                  <button
                    onClick={() => setInputMode('text')}
                    className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                      inputMode === 'text'
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    Text Notes
                  </button>
                  <button
                    onClick={() => setInputMode('voice')}
                    className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                      inputMode === 'voice'
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    Voice Note
                  </button>
                </div>

                {inputMode === 'text' ? (
                  <textarea
                    placeholder="Describe what happened during your consultation, what the doctor told you, what you understood, any questions you still have..."
                    value={form.summary}
                    onChange={(e) => updateField('summary', e.target.value)}
                    rows={8}
                    className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none leading-relaxed"
                  />
                ) : (
                  <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 flex flex-col items-center gap-4">
                    {/* Recording button */}
                    <button
                      onClick={isRecording ? stopRecording : startRecording}
                      className={`w-20 h-20 rounded-full flex items-center justify-center transition-all shadow-lg ${
                        isRecording
                          ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                          : 'bg-blue-600 hover:bg-blue-700'
                      }`}
                    >
                      {isRecording ? (
                        <MicOff size={28} className="text-white" />
                      ) : (
                        <Mic size={28} className="text-white" />
                      )}
                    </button>

                    {isRecording && (
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                        <span className="text-sm font-mono text-red-500 font-medium">
                          {formatTime(recordingTime)}
                        </span>
                      </div>
                    )}

                    <p className="text-sm text-slate-500 text-center">
                      {isRecording
                        ? 'Recording... Click to stop'
                        : voiceBlob
                        ? 'Recording saved! Click to re-record'
                        : 'Click to start recording your voice note'}
                    </p>

                    {voiceBlob && !isRecording && (
                      <div className="flex items-center gap-2 px-4 py-2.5 bg-blue-50 rounded-lg border border-blue-200">
                        <CheckCircle2 size={16} className="text-blue-600" />
                        <span className="text-sm text-blue-700 font-medium">
                          Voice note recorded ({formatTime(recordingTime)}s)
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {!form.summary && !voiceBlob && (
                <div className="flex items-start gap-2 px-3 py-2.5 bg-amber-50 rounded-lg border border-amber-200">
                  <AlertCircle size={15} className="text-amber-500 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-amber-700">
                    Please add text notes or record a voice note to continue.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Documents */}
          {step === 3 && (
            <div className="space-y-4">
              <p className="text-sm text-slate-600">
                Upload any documents from your consultation — prescriptions, lab results, imaging reports, etc.
              </p>

              {/* Drop zone */}
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={onDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center gap-3 cursor-pointer transition-all ${
                  isDragOver
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center">
                  <Upload size={22} className="text-slate-400" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-700">Drop files here or click to browse</p>
                  <p className="text-xs text-slate-400 mt-1">PDF, JPG, PNG, DOCX up to 10MB each</p>
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

              {/* File list */}
              {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                    Uploaded ({uploadedFiles.length})
                  </p>
                  {uploadedFiles.map((file) => (
                    <div
                      key={file.name}
                      className="flex items-center gap-3 px-3.5 py-2.5 bg-slate-50 rounded-lg border border-slate-200"
                    >
                      <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                        <FileText size={14} className="text-blue-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-800 truncate">{file.name}</p>
                        <p className="text-xs text-slate-400">{formatFileSize(file.size)}</p>
                      </div>
                      <button
                        onClick={() => removeFile(file.name)}
                        className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {uploadedFiles.length === 0 && (
                <p className="text-sm text-center text-slate-400 py-2">
                  Documents are optional — you can always add them later.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-white space-y-3">
          {submitError && (
            <div className="flex items-start gap-2 px-3 py-2.5 bg-red-50 rounded-lg border border-red-200">
              <AlertCircle size={15} className="text-red-500 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-red-700">{submitError}</p>
            </div>
          )}
          <div className="flex items-center justify-between">
            <button
              onClick={() => step > 1 ? setStep((s) => (s - 1) as Step) : onClose()}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors disabled:opacity-40"
            >
              {step === 1 ? 'Cancel' : 'Back'}
            </button>

            <div className="flex items-center gap-3">
              <div className="flex gap-1.5">
                {[1, 2, 3].map((n) => (
                  <div
                    key={n}
                    className={`w-1.5 h-1.5 rounded-full transition-all ${
                      n === step ? 'bg-blue-600 w-4' : n < step ? 'bg-blue-300' : 'bg-slate-200'
                    }`}
                  />
                ))}
              </div>

              {step < 3 ? (
                <button
                  onClick={() => setStep((s) => (s + 1) as Step)}
                  disabled={step === 1 ? !isStep1Valid : !isStep2Valid}
                  className="flex items-center gap-2 px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                  Continue
                  <ChevronRight size={15} />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="flex items-center gap-2 px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 size={15} className="animate-spin" />
                      Creating…
                    </>
                  ) : (
                    <>
                      <CheckCircle2 size={15} />
                      Create Case
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
