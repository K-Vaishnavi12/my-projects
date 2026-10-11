import type {
  MetadataResponse,
  PatientPayload,
  PredictResponse,
  RecommendResponse,
} from './types';

const API_BASE =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => request<{ status: string }>('/health'),
  metadata: () => request<MetadataResponse>('/metadata'),
  predict: (p: PatientPayload) =>
    request<PredictResponse>('/predict', {
      method: 'POST',
      body: JSON.stringify(p),
    }),
  recommend: (
    patient: PatientPayload,
    opts: {
      candidate_doctors?: string[];
      horizon_hours?: number;
      step_minutes?: number;
      top_k?: number;
    } = {},
  ) =>
    request<RecommendResponse>('/recommend', {
      method: 'POST',
      body: JSON.stringify({ patient, ...opts }),
    }),
};

export { API_BASE };
