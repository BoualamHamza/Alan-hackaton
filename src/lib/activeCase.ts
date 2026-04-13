import { mockCases } from './mockData';
import { MedicalCase } from '@/types';

/**
 * The "active case" is the one all global tabs (Home, Reels, Games, Metrics)
 * render against. For now it's always the first mock case so the demo works
 * without a backend; later this can read from localStorage or the API.
 */
export function getActiveCase(): MedicalCase {
  return mockCases[0];
}
