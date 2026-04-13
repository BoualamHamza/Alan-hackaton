import type { Metadata, Viewport } from 'next';
import { Poppins } from 'next/font/google';
import { Suspense } from 'react';
import './globals.css';
import MobileHeader from '@/components/MobileHeader';
import BottomNav from '@/components/BottomNav';
import CreateCaseLauncher from '@/components/CreateCaseLauncher';
import ServiceWorkerRegister from '@/components/ServiceWorkerRegister';

const poppins = Poppins({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-poppins',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Hippo — Your Health Companion',
  description: 'Track your health, watch explainers, and chat with Hippo AI.',
  manifest: '/manifest.webmanifest',
  appleWebApp: {
    capable: true,
    title: 'Hippo',
    statusBarStyle: 'default',
  },
  icons: {
    icon: '/logo.jpeg',
    apple: '/icons/apple-touch-icon.png',
  },
};

export const viewport: Viewport = {
  themeColor: '#fab9d1',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  viewportFit: 'cover',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={poppins.variable}>
      <body className="font-[var(--font-poppins)] bg-hippo-bg text-hippo-ink min-h-screen">
        <div className="relative z-10 mx-auto w-full max-w-md min-h-screen flex flex-col">
          <Suspense fallback={null}>
            <MobileHeader />
          </Suspense>
          <main className="flex-1 px-5 pb-32 pt-2">
            {children}
          </main>
          <Suspense fallback={null}>
            <BottomNav />
          </Suspense>
        </div>
        <Suspense fallback={null}>
          <CreateCaseLauncher />
        </Suspense>
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
