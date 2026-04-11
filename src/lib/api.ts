import { MedicalCase } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export { API_BASE };

export async function createCase(formData: FormData): Promise<MedicalCase> {
  const res = await fetch(`${API_BASE}/cases`, {
    method: 'POST',
    body: formData,
    // Do NOT set Content-Type — the browser sets it with the correct multipart boundary
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? 'Failed to create case');
  }
  return res.json();
}

export async function getCase(id: string): Promise<MedicalCase> {
  const res = await fetch(`${API_BASE}/cases/${id}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Case ${id} not found`);
  return res.json();
}
