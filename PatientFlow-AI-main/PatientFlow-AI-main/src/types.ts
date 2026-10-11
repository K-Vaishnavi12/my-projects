export interface DoctorMeta {
  id: string;
  specialty: string;
  mean_service_min: number;
}

export interface AppointmentTypeMeta {
  id: string;
  no_show_base: number;
}

export interface ModelMetrics {
  classifier?: {
    xgb_calibrated?: {
      roc_auc: number;
      pr_auc: number;
      brier: number;
      f1: number;
      threshold: number;
    };
    logreg_baseline?: {
      roc_auc: number;
      pr_auc: number;
    };
  };
  regressor?: {
    mae_p50: number;
    rmse_p50: number;
    pinball_p10: number;
    pinball_p50: number;
    pinball_p90: number;
    coverage_80pct_interval: number;
  };
}

export interface MetadataResponse {
  doctors: DoctorMeta[];
  appointment_types: AppointmentTypeMeta[];
  metrics: ModelMetrics;
  threshold: number;
}

// ---------- ephemeral prediction payload ----------
export interface PatientPayload {
  doctor_id: string;
  appointment_type: string;
  appointment_time: string; // ISO string
  age: number;
  sex: string;
  has_insurance: boolean;
  lead_time_days: number;
  prior_no_shows: number;
  prior_visits: number;
  sms_reminder: boolean;
}

export interface WaitOut {
  p10: number;
  p50: number;
  p90: number;
}

export interface PredictResponse {
  id?: number;
  cancellation_prob: number;
  cancellation_threshold: number;
  cancellation_flag: boolean;
  expected_wait_minutes: WaitOut;
  interpretation: string;
}

export interface SlotOut {
  appointment_time: string;
  doctor_id: string;
  expected_wait: WaitOut;
  cancellation_prob: number;
  score: number;
  rationale: string;
}

export interface RecommendResponse {
  run_id?: number;
  recommendations: SlotOut[];
}

// ---------- SQL entities ----------
export interface PatientOut {
  id: number;
  full_name: string;
  age: number;
  sex: string;
  email: string | null;
  phone: string | null;
  has_insurance: boolean;
  prior_visits: number;
  prior_no_shows: number;
  sms_reminder: boolean;
  created_at: string;
}

export interface PatientCreate {
  full_name: string;
  age: number;
  sex: string;
  email?: string | null;
  phone?: string | null;
  has_insurance: boolean;
  prior_visits: number;
  prior_no_shows: number;
  sms_reminder: boolean;
}

export type PatientUpdate = Partial<PatientCreate>;

export interface AppointmentOut {
  id: number;
  patient_id: number;
  doctor_id: string;
  appointment_type_id: string;
  appointment_time: string;
  lead_time_days: number;
  status: string;
  notes: string | null;
  created_at: string;
}

export interface AppointmentCreate {
  patient_id: number;
  doctor_id: string;
  appointment_type_id: string;
  appointment_time: string;
  lead_time_days: number;
  status?: string;
  notes?: string | null;
}

export type AppointmentUpdate = Partial<Omit<AppointmentCreate, 'patient_id'>>;

export interface PredictionOut {
  id: number;
  appointment_id: number | null;
  patient_id: number | null;
  cancellation_prob: number;
  cancellation_flag: boolean;
  wait_p10: number;
  wait_p50: number;
  wait_p90: number;
  interpretation: string;
  created_at: string;
}

// ---------- stats ----------
export interface StatusCount {
  status: string;
  count: number;
}
export interface DoctorLoad {
  doctor_id: string;
  specialty: string;
  total: number;
  completed: number;
  cancelled: number;
  no_show: number;
}
export interface RevenueByType {
  appointment_type_id: string;
  invoices: number;
  total_amount: number;
}
export interface StatsResponse {
  totals: {
    patients: number;
    appointments: number;
    doctors: number;
    invoices: number;
    revenue_paid: number;
    revenue_pending: number;
  };
  appointments_by_status: StatusCount[];
  doctor_load: DoctorLoad[];
  revenue_by_type: RevenueByType[];
  top_no_show_patients: { patient_id: number; full_name: string; no_shows: number }[];
}
