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
  recommendations: SlotOut[];
}
