import { Activity, Wifi, WifiOff } from 'lucide-react';
import { useEffect, useState } from 'react';
import { API_BASE, api } from './api';
import { MetricsPanel } from './components/MetricsPanel';
import { PatientForm } from './components/PatientForm';
import { PredictionCard } from './components/PredictionCard';
import { RecommendationList } from './components/RecommendationList';
import type {
  MetadataResponse,
  PatientPayload,
  PredictResponse,
  SlotOut,
} from './types';

function App() {
  const [meta, setMeta] = useState<MetadataResponse | null>(null);
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [recs, setRecs] = useState<SlotOut[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await api.health();
        const m = await api.metadata();
        if (cancelled) return;
        setHealthy(true);
        setMeta(m);
      } catch (e) {
        if (cancelled) return;
        setHealthy(false);
        setError((e as Error).message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const onPredict = async (payload: PatientPayload) => {
    setLoading(true);
    setError(null);
    try {
      const r = await api.predict(payload);
      setPrediction(r);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const onRecommend = async (payload: PatientPayload) => {
    setLoading(true);
    setError(null);
    try {
      const r = await api.recommend(payload, {
        horizon_hours: 48,
        step_minutes: 60,
        top_k: 6,
      });
      setRecs(r.recommendations);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white grid place-items-center">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900">PatientFlow AI</h1>
              <p className="text-xs text-slate-500">
                Multi-task ML for cancellation risk + quantile wait-time forecasting
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="hidden sm:inline">API:</span>
            <code className="px-2 py-1 rounded bg-slate-100 text-slate-700">{API_BASE}</code>
            {healthy === true && (
              <span className="flex items-center gap-1 text-emerald-600">
                <Wifi className="w-3 h-3" /> connected
              </span>
            )}
            {healthy === false && (
              <span className="flex items-center gap-1 text-rose-600">
                <WifiOff className="w-3 h-3" /> offline
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6 space-y-6">
        {error && (
          <div className="rounded-xl bg-rose-50 border border-rose-200 text-rose-800 p-4 text-sm">
            <strong>Error:</strong> {error}
            <p className="mt-1 text-xs text-rose-700">
              Make sure the FastAPI backend is running:{' '}
              <code className="px-1 rounded bg-white">
                .venv\Scripts\python -m uvicorn api.main:app --reload
              </code>
            </p>
          </div>
        )}

        {meta?.metrics && <MetricsPanel metrics={meta.metrics} />}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PatientForm
            doctors={meta?.doctors ?? []}
            appointmentTypes={meta?.appointment_types ?? []}
            loading={loading}
            onPredict={onPredict}
            onRecommend={onRecommend}
          />
          <div className="space-y-6">
            <PredictionCard result={prediction} />
            <RecommendationList recommendations={recs} />
          </div>
        </div>

        <footer className="text-center text-xs text-slate-400 pt-4">
          Models are trained on a synthetic outpatient dataset with known causal
          structure. ROC-AUC, PR-AUC, pinball loss and interval coverage are computed
          on a temporally held-out 20% test fold.
        </footer>
      </main>
    </div>
  );
}

export default App;
