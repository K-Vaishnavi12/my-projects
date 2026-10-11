import { AlertTriangle, CheckCircle2, Gauge, Timer } from 'lucide-react';
import type { PredictResponse } from '../types';

interface Props {
  result: PredictResponse | null;
}

export function PredictionCard({ result }: Props) {
  if (!result) {
    return (
      <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-500">
        Submit the form to see a calibrated prediction with quantile uncertainty.
      </div>
    );
  }

  const { cancellation_prob, cancellation_threshold, cancellation_flag, expected_wait_minutes, interpretation } =
    result;
  const { p10, p50, p90 } = expected_wait_minutes;

  const cancelPct = (cancellation_prob * 100).toFixed(1);
  const thrPct = (cancellation_threshold * 100).toFixed(1);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">Prediction</h2>
          <p className="text-sm text-slate-500">{interpretation}</p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium ${
            cancellation_flag
              ? 'bg-amber-100 text-amber-800'
              : 'bg-emerald-100 text-emerald-800'
          }`}
        >
          {cancellation_flag ? (
            <span className="flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> flagged
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> low risk
            </span>
          )}
        </span>
      </div>

      {/* Cancellation gauge */}
      <div>
        <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
          <span className="flex items-center gap-1">
            <Gauge className="w-3 h-3" /> Cancellation probability
          </span>
          <span>
            {cancelPct}% (threshold {thrPct}%)
          </span>
        </div>
        <div className="h-3 rounded-full bg-slate-100 relative overflow-hidden">
          <div
            className={`h-full ${
              cancellation_flag ? 'bg-amber-500' : 'bg-indigo-500'
            }`}
            style={{ width: `${Math.min(100, cancellation_prob * 100)}%` }}
          />
          <div
            className="absolute top-0 bottom-0 w-px bg-slate-700"
            style={{ left: `${Math.min(100, cancellation_threshold * 100)}%` }}
          />
        </div>
      </div>

      {/* Wait-time quantile band */}
      <div>
        <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
          <span className="flex items-center gap-1">
            <Timer className="w-3 h-3" /> Expected wait (P10 - P50 - P90)
          </span>
          <span>
            {p10.toFixed(1)} - <span className="font-semibold text-slate-700">{p50.toFixed(1)}</span> -{' '}
            {p90.toFixed(1)} min
          </span>
        </div>
        <QuantileBand p10={p10} p50={p50} p90={p90} />
      </div>

      <p className="text-xs text-slate-400">
        Probabilities are isotonic-calibrated. Wait quantiles come from three LightGBM
        models trained with quantile loss; empirical [P10, P90] interval coverage was
        ~80% on held-out data.
      </p>
    </div>
  );
}

function QuantileBand({ p10, p50, p90 }: { p10: number; p50: number; p90: number }) {
  const max = Math.max(60, p90 * 1.2);
  const left = (p10 / max) * 100;
  const width = ((p90 - p10) / max) * 100;
  const median = (p50 / max) * 100;
  return (
    <div className="h-3 rounded-full bg-slate-100 relative overflow-hidden">
      <div
        className="absolute top-0 bottom-0 bg-indigo-200"
        style={{ left: `${left}%`, width: `${Math.max(0, width)}%` }}
      />
      <div
        className="absolute top-0 bottom-0 w-1 bg-indigo-600"
        style={{ left: `${median}%` }}
      />
    </div>
  );
}
