import type { Metadata } from 'next';
import { Suspense } from 'react';
import './globals.css';
import Navbar from '@/components/Navbar';
import AIAssistant from '@/components/AIAssistant';

export const metadata: Metadata = {
  title: 'HealthPath — Your Personal Health Dashboard',
  description: 'Understand your health journey after every consultation with AI-powered insights.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50">
        <Suspense>
          <Navbar />
        </Suspense>
        <main className="ml-56 min-h-screen">
          {children}
        </main>
        <AIAssistant />
      </body>
    </html>
  );
}
