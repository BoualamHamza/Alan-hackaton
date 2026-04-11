export type VideoStatus = 'pending' | 'processing' | 'ready' | 'error';

export interface VideoInfo {
  id: string;
  title: string;
  url: string;
}

export interface MedicalCase {
  id: string;
  title: string;
  specialty: string;
  doctorName: string;
  visitDate: string;
  summary: string;
  symptoms: string[];
  createdAt: string;
  updatedAt: string;
  documentsCount: number;
  hasVoiceNote: boolean;
  // Video generation fields — optional so mock data stays valid
  videoStatus?: VideoStatus;
  videos?: VideoInfo[] | null;
  errorMessage?: string | null;
}

export interface CreateCaseFormData {
  title: string;
  specialty: string;
  doctorName: string;
  visitDate: string;
  summary: string;
  symptoms: string;
  voiceNote: Blob | null;
  documents: File[];
}
