import { CalendarClock, ChevronRight, Sparkles } from 'lucide-react';
import type { SlotOut } from '../types';

interface Props {
  recommendations: SlotOut[];
}

const fmt = (iso: string) => {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
};

export function RecommendationList({ recommendations }: Props) {
  if (!recommendations.length) {
    return (
      <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-500">
        Click "Recommend optimal slots" to score the next 48h with the model.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-600" /> Recommended slots
        </h2>
        <span className="text-xs text-slate-500">lower score = better</span>
      </div>

      <ol className="space-y-2">
        {recommendations.map((r, idx) => (
          <li
            key={`${r.appointment_time}-${r.doctor_id}`}
            className="border border-slate-200 rounded-xl p-4 hover:border-indigo-400 transition"
          >
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 font-semibold text-sm flex items-center justify-center">
                  {idx + 1}
                </span>
                <div>
                  <div className="flex items-center gap-2 text-slate-800 font-medium">
                    <CalendarClock className="w-4 h-4 text-slate-500" />
                    {fmt(r.appointment_time)}
                  </div>
                  <div className="text-xs text-slate-500">
                    {r.doctor_id.split('_').slice(2).join(' ')} - {r.doctor_id.split('_')[1]}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-slate-700">
                  P50 wait <span className="font-semibold">{r.expected_wait.p50.toFixed(1)} min</span>
                </div>
                <div className="text-xs text-slate-500">
                  P10-P90: {r.expected_wait.p10.toFixed(1)} - {r.expected_wait.p90.toFixed(1)} min
                </div>
              </div>
            </div>
            <div className="mt-2 flex items-center justify-between text-xs">
              <span className="text-slate-500">
                cancel risk{' '}
                <span className="font-medium text-slate-700">
                  {(r.cancellation_prob * 100).toFixed(1)}%
                </span>{' '}
                <ChevronRight className="inline w-3 h-3 -mb-0.5" /> score{' '}
                <span className="font-medium text-slate-700">{r.score.toFixed(2)}</span>
              </span>
              <span className="text-slate-400 italic">{r.rationale}</span>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
