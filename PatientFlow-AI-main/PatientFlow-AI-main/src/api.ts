import type {
  AppointmentOut,
  AppointmentCreate,
  AppointmentUpdate,
  MetadataResponse,
  PatientCreate,
  PatientOut,
  PatientPayload,
  PatientUpdate,
  PredictResponse,
  PredictionOut,
  RecommendResponse,
  StatsResponse,
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
  if (res.status === 204) return undefined as unknown as T;
  return (await res.json()) as T;
}

export const api = {
  // meta
  health: () => request<{ status: string; db: boolean }>('/health'),
  metadata: () => request<MetadataResponse>('/metadata'),

  // patients
  listPatients: () => request<PatientOut[]>('/patients'),
  getPatient: (id: number) => request<PatientOut>(`/patients/${id}`),
  createPatient: (p: PatientCreate) =>
    request<PatientOut>('/patients', { method: 'POST', body: JSON.stringify(p) }),
  updatePatient: (id: number, p: PatientUpdate) =>
    request<PatientOut>(`/patients/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(p),
    }),
  deletePatient: (id: number) =>
    request<void>(`/patients/${id}`, { method: 'DELETE' }),

  // appointments
  listAppointments: (params: {
    patient_id?: number;
    doctor_id?: string;
    status_?: string;
  } = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v != null && qs.append(k, String(v)));
    const s = qs.toString();
    return request<AppointmentOut[]>(`/appointments${s ? `?${s}` : ''}`);
  },
  createAppointment: (a: AppointmentCreate) =>
    request<AppointmentOut>('/appointments', {
      method: 'POST',
      body: JSON.stringify(a),
    }),
  updateAppointment: (id: number, a: AppointmentUpdate) =>
    request<AppointmentOut>(`/appointments/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(a),
    }),
  deleteAppointment: (id: number) =>
    request<void>(`/appointments/${id}`, { method: 'DELETE' }),

  // ml
  predict: (
    payload: PatientPayload,
    opts: { patient_id?: number; appointment_id?: number; persist?: boolean } = {},
  ) =>
    request<PredictResponse>('/predict', {
      method: 'POST',
      body: JSON.stringify({ payload, ...opts }),
    }),
  recommend: (
    patient: PatientPayload,
    opts: {
      patient_id?: number;
      candidate_doctors?: string[];
      horizon_hours?: number;
      step_minutes?: number;
      top_k?: number;
      persist?: boolean;
    } = {},
  ) =>
    request<RecommendResponse>('/recommend', {
      method: 'POST',
      body: JSON.stringify({ patient, ...opts }),
    }),
  listPredictions: (params: { patient_id?: number; appointment_id?: number } = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v != null && qs.append(k, String(v)));
    const s = qs.toString();
    return request<PredictionOut[]>(`/predictions${s ? `?${s}` : ''}`);
  },

  // stats
  stats: () => request<StatsResponse>('/stats'),
};

export { API_BASE };
