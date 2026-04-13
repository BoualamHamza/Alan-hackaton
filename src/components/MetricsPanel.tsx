'use client';

import { TrendingUp, TrendingDown, Minus, Sparkles } from 'lucide-react';

interface MetricsPanelProps {
  specialty: string;
}

export default function MetricsPanel({ specialty }: MetricsPanelProps) {
  const metrics = [
    { label: 'Pain Level', value: '4/10', trend: 'down', change: '−2 from last visit' },
    { label: 'Sleep Quality', value: '6.5h', trend: 'up', change: '+1h avg' },
    { label: 'Activity Score', value: '72%', trend: 'up', change: '+8% this week' },
    { label: 'Medication', value: '89%', trend: 'stable', change: 'Adherence' },
  ];

  const timeline = [
    { date: 'Apr 8', event: 'Consultation', note: 'Initial diagnosis, MRI ordered' },
    { date: 'Apr 15', event: 'MRI Scan', note: 'Results pending' },
    { date: 'Apr 22', event: 'Follow-up', note: 'Review MRI results' },
    { date: 'May 10', event: 'PT Session 1', note: 'Physical therapy begins' },
  ];

  const trendIcon = (t: string) =>
    t === 'up' ? (
      <TrendingUp size={12} className="text-emerald-500" strokeWidth={3} />
    ) : t === 'down' ? (
      <TrendingDown size={12} className="text-emerald-500" strokeWidth={3} />
    ) : (
      <Minus size={12} className="text-hippo-ink-soft" strokeWidth={3} />
    );

  return (
    <div className="space-y-5">
      {/* Metric grid */}
      <div>
        <h2 className="text-[13px] font-bold text-hippo-ink mb-3 px-1">Key health metrics</h2>
        <div className="grid grid-cols-2 gap-3">
          {metrics.map((m) => (
            <div
              key={m.label}
              className="bg-white rounded-[20px] p-4 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)]"
            >
              <p className="text-[10px] font-bold text-hippo-ink-soft uppercase tracking-wide">{m.label}</p>
              <p className="text-[22px] font-extrabold text-hippo-ink mt-1 leading-none">{m.value}</p>
              <div className="flex items-center gap-1 mt-2">
                {trendIcon(m.trend)}
                <span className="text-[10px] font-medium text-hippo-ink-soft">{m.change}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Symptom trend */}
      <div className="bg-white rounded-[24px] p-5 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)]">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[13px] font-bold text-hippo-ink">Symptom trend</h3>
          <span className="text-[10px] text-hippo-ink-soft font-medium">Last 14 days</span>
        </div>
        <div className="flex items-end gap-1.5 h-24">
          {[7, 6, 8, 5, 7, 4, 6, 5, 4, 4, 5, 3, 4, 3].map((v, i) => (
            <div key={i} className="flex-1 flex flex-col items-center">
              <div
                className="w-full rounded-t-lg bg-gradient-to-t from-hippo-pink to-hippo-pink-hot transition-all"
                style={{ height: `${(v / 10) * 100}%` }}
              />
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2">
          <span className="text-[10px] text-hippo-ink-soft">Mar 28</span>
          <span className="text-[10px] text-hippo-ink-soft">Apr 10</span>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-white rounded-[24px] p-5 shadow-[0_8px_24px_-12px_rgba(244,140,186,0.4)]">
        <h3 className="text-[13px] font-bold text-hippo-ink mb-4">Care timeline</h3>
        <div className="space-y-0">
          {timeline.map((item, i) => (
            <div key={i} className="flex gap-3">
              <div className="flex flex-col items-center">
                <div className="w-2.5 h-2.5 rounded-full bg-hippo-pink-hot mt-1.5 flex-shrink-0 ring-4 ring-hippo-pink-soft" />
                {i < timeline.length - 1 && <div className="w-0.5 flex-1 bg-hippo-pink-soft my-1" />}
              </div>
              <div className="pb-4 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-hippo-pink-hot">{item.date}</span>
                  <span className="text-[13px] font-bold text-hippo-ink">{item.event}</span>
                </div>
                <p className="text-[11px] text-hippo-ink-soft mt-0.5">{item.note}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI insight */}
      <div className="bg-gradient-to-br from-hippo-pink-soft to-hippo-pink rounded-[24px] p-5">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-2xl bg-white flex items-center justify-center flex-shrink-0 shadow-sm">
            <Sparkles size={18} className="text-hippo-pink-hot" strokeWidth={2.5} />
          </div>
          <div>
            <p className="text-[13px] font-bold text-hippo-ink mb-1">AI health insight</p>
            <p className="text-[12px] text-hippo-ink leading-relaxed">
              Based on your {specialty.toLowerCase()} case, symptoms show gradual improvement over the past 2 weeks.
              Keep up your physical therapy and medication routine — it&apos;s working.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
