import { useState } from 'react';
import { api } from '../api';
import { MetricsPanel } from '../components/MetricsPanel';
import { PatientForm } from '../components/PatientForm';
import { PredictionCard } from '../components/PredictionCard';
import { RecommendationList } from '../components/RecommendationList';
import type {
  MetadataResponse,
  PatientPayload,
  PredictResponse,
  SlotOut,
} from '../types';

interface Props {
  meta: MetadataResponse | null;
}

export function PredictPage({ meta }: Props) {
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [recs, setRecs] = useState<SlotOut[]>([]);
  const [error, setError] = useState<string | null>(null);

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
    <div className="space-y-6">
      {error && (
        <div className="rounded-xl bg-rose-50 border border-rose-200 text-rose-800 p-3 text-sm">
          {error}
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
    </div>
  );
}
