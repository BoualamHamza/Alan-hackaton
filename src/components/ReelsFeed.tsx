'use client';

import { useState, useEffect } from 'react';
import { Loader2, AlertCircle, Play, Film } from 'lucide-react';
import { mockCases } from '@/lib/mockData';
import { getCase, API_BASE } from '@/lib/api';
import { VideoStatus, VideoInfo } from '@/types';

const isMockCase = (id: string) => mockCases.some((c) => c.id === id);

function useVideoPolling(caseId: string) {
  const [videoStatus, setVideoStatus] = useState<VideoStatus | undefined>(undefined);
  const [videos, setVideos] = useState<VideoInfo[] | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isMock] = useState(() => isMockCase(caseId));

  useEffect(() => {
    if (isMock) return;
    let cancelled = false;

    const poll = async () => {
      try {
        const data = await getCase(caseId);
        if (cancelled) return;
        setVideoStatus(data.videoStatus);
        setVideos(data.videos ?? null);
        setErrorMessage(data.errorMessage ?? null);
      } catch {
        /* keep polling */
      }
    };

    poll();
    const interval = setInterval(() => {
      if (videoStatus === 'ready' || videoStatus === 'error') return;
      poll();
    }, 5000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId, videoStatus]);

  return { videoStatus, videos, errorMessage, isMock };
}

interface ReelsFeedProps {
  caseId: string;
}

export default function ReelsFeed({ caseId }: ReelsFeedProps) {
  const { videoStatus, videos, errorMessage, isMock } = useVideoPolling(caseId);

  if (isMock) {
    // Demo placeholder reels so the UI looks alive without a backend
    return (
      <div className="space-y-4">
        <PlaceholderReel title="Understanding Cholesterol" subtitle="5 things your doctor wants you to know" emoji="👩‍⚕️" />
        <PlaceholderReel title="Managing Blood Pressure" subtitle="Daily habits that actually help" emoji="🫀" />
        <PlaceholderReel title="What is HbA1c?" subtitle="Your 3-month sugar story" emoji="🩸" />
      </div>
    );
  }

  if (videoStatus === undefined || videoStatus === 'pending' || videoStatus === 'processing') {
    return (
      <div className="space-y-4">
        <div className="bg-white rounded-[24px] p-5 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)] flex items-start gap-3">
          <Loader2 size={18} className="text-hippo-pink-hot animate-spin mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-bold text-hippo-ink">Generating your reels…</p>
            <p className="text-[11px] text-hippo-ink-soft mt-1">
              We&apos;re creating two AI videos tailored to your consultation. This takes 2–5 minutes.
            </p>
          </div>
        </div>
        {[0, 1].map((i) => (
          <div key={i} className="bg-white rounded-[24px] overflow-hidden shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)] animate-pulse">
            <div className="aspect-[9/14] bg-hippo-pink-soft" />
            <div className="p-4 space-y-2">
              <div className="h-3 bg-hippo-pink-soft rounded w-1/3" />
              <div className="h-4 bg-hippo-pink-soft rounded w-3/4" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (videoStatus === 'error') {
    return (
      <div className="bg-white rounded-[24px] p-5 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)] flex items-start gap-3">
        <AlertCircle size={18} className="text-red-500 mt-0.5 flex-shrink-0" />
        <div>
          <p className="text-sm font-bold text-hippo-ink">Video generation failed</p>
          {errorMessage && <p className="text-[11px] text-hippo-ink-soft mt-1 font-mono">{errorMessage}</p>}
          <p className="text-[11px] text-hippo-ink-soft mt-1">Please try creating the case again.</p>
        </div>
      </div>
    );
  }

  if (videoStatus === 'ready' && videos && videos.length > 0) {
    return (
      <div className="space-y-4">
        {videos.map((v, idx) => (
          <div
            key={v.id}
            className="bg-white rounded-[24px] overflow-hidden shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)]"
          >
            <video
              controls
              preload="metadata"
              crossOrigin="anonymous"
              className="w-full aspect-[9/14] object-cover bg-black"
              src={`${API_BASE}/cases/${caseId}/videos/${idx + 1}`}
            >
              Your browser does not support video playback.
            </video>
            <div className="p-4 flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-hippo-pink-soft flex items-center justify-center flex-shrink-0">
                <Film size={16} className="text-hippo-pink-hot" />
              </div>
              <p className="text-[13px] font-bold text-hippo-ink leading-tight">{v.title}</p>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return null;
}

function PlaceholderReel({ title, subtitle, emoji }: { title: string; subtitle: string; emoji: string }) {
  return (
    <div className="bg-white rounded-[24px] overflow-hidden shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)]">
      <div className="aspect-[9/14] bg-gradient-to-br from-hippo-pink-soft via-hippo-pink to-hippo-pink-hot relative flex items-center justify-center">
        <span className="text-[88px]">{emoji}</span>
        <button
          aria-label="Play reel"
          className="absolute w-16 h-16 rounded-full bg-white/90 backdrop-blur-sm flex items-center justify-center shadow-[0_8px_24px_-6px_rgba(0,0,0,0.3)] active:scale-95 transition-transform"
        >
          <Play size={22} className="text-hippo-pink-hot ml-1" fill="currentColor" />
        </button>
        <div className="absolute bottom-4 left-4 right-4 text-white">
          <p className="text-xs opacity-90">{subtitle}</p>
          <p className="text-base font-bold leading-tight mt-0.5 drop-shadow">{title}</p>
        </div>
      </div>
    </div>
  );
}
