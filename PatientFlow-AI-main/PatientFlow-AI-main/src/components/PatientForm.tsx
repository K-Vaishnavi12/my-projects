import { useEffect, useState } from 'react';
import type { AppointmentTypeMeta, DoctorMeta, PatientPayload } from '../types';

interface Props {
  doctors: DoctorMeta[];
  appointmentTypes: AppointmentTypeMeta[];
  loading: boolean;
  onPredict: (payload: PatientPayload) => void;
  onRecommend: (payload: PatientPayload) => void;
}

const todayPlus = (days: number, hour = 10): string => {
  const d = new Date();
  d.setDate(d.getDate() + days);
  d.setHours(hour, 0, 0, 0);
  // Local-time ISO without TZ offset (FastAPI parses via fromisoformat)
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours(),
  )}:${pad(d.getMinutes())}`;
};

export function PatientForm({
  doctors,
  appointmentTypes,
  loading,
  onPredict,
  onRecommend,
}: Props) {
  const [doctorId, setDoctorId] = useState('');
  const [apptType, setApptType] = useState('');
  const [apptTime, setApptTime] = useState(todayPlus(2, 10));
  const [age, setAge] = useState(38);
  const [sex, setSex] = useState('F');
  const [hasInsurance, setHasInsurance] = useState(true);
  const [leadDays, setLeadDays] = useState(2);
  const [priorNoShows, setPriorNoShows] = useState(0);
  const [priorVisits, setPriorVisits] = useState(3);
  const [sms, setSms] = useState(true);

  useEffect(() => {
    if (!doctorId && doctors.length) setDoctorId(doctors[0].id);
  }, [doctors, doctorId]);
  useEffect(() => {
    if (!apptType && appointmentTypes.length)
      setApptType(appointmentTypes[0].id);
  }, [appointmentTypes, apptType]);

  const buildPayload = (): PatientPayload => ({
    doctor_id: doctorId,
    appointment_type: apptType,
    appointment_time: apptTime,
    age,
    sex,
    has_insurance: hasInsurance,
    lead_time_days: leadDays,
    prior_no_shows: priorNoShows,
    prior_visits: priorVisits,
    sms_reminder: sms,
  });

  return (
    <form
      className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        onPredict(buildPayload());
      }}
    >
      <div>
        <h2 className="text-lg font-semibold text-slate-800">Patient + appointment</h2>
        <p className="text-sm text-slate-500">
          Provide observable features. Models predict cancellation risk and wait quantiles.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Doctor">
          <select
            className="select"
            value={doctorId}
            onChange={(e) => setDoctorId(e.target.value)}
          >
            {doctors.map((d) => (
              <option key={d.id} value={d.id}>
                {d.id.split('_').slice(2).join(' ')} - {d.specialty}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Appointment type">
          <select
            className="select"
            value={apptType}
            onChange={(e) => setApptType(e.target.value)}
          >
            {appointmentTypes.map((t) => (
              <option key={t.id} value={t.id}>
                {t.id.replace('_', ' ')} (base no-show {(t.no_show_base * 100).toFixed(0)}%)
              </option>
            ))}
          </select>
        </Field>
        <Field label="Appointment time">
          <input
            className="input"
            type="datetime-local"
            value={apptTime}
            onChange={(e) => setApptTime(e.target.value)}
            required
          />
        </Field>
        <Field label="Lead time (days)">
          <input
            className="input"
            type="number"
            min={0}
            value={leadDays}
            onChange={(e) => setLeadDays(parseInt(e.target.value || '0', 10))}
          />
        </Field>
        <Field label="Age">
          <input
            className="input"
            type="number"
            min={0}
            max={120}
            value={age}
            onChange={(e) => setAge(parseInt(e.target.value || '0', 10))}
          />
        </Field>
        <Field label="Sex">
          <select className="select" value={sex} onChange={(e) => setSex(e.target.value)}>
            <option value="F">F</option>
            <option value="M">M</option>
            <option value="O">O</option>
          </select>
        </Field>
        <Field label="Prior visits">
          <input
            className="input"
            type="number"
            min={0}
            value={priorVisits}
            onChange={(e) => setPriorVisits(parseInt(e.target.value || '0', 10))}
          />
        </Field>
        <Field label="Prior no-shows">
          <input
            className="input"
            type="number"
            min={0}
            value={priorNoShows}
            onChange={(e) => setPriorNoShows(parseInt(e.target.value || '0', 10))}
          />
        </Field>
      </div>

      <div className="flex flex-wrap gap-4 pt-2">
        <Toggle label="Has insurance" value={hasInsurance} onChange={setHasInsurance} />
        <Toggle label="SMS reminder" value={sms} onChange={setSms} />
      </div>

      <div className="flex flex-wrap gap-3 pt-3">
        <button
          type="submit"
          className="btn-primary"
          disabled={loading || !doctorId || !apptType}
        >
          Predict for this slot
        </button>
        <button
          type="button"
          className="btn-secondary"
          disabled={loading || !doctorId || !apptType}
          onClick={() => onRecommend(buildPayload())}
        >
          Recommend optimal slots
        </button>
      </div>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="text-sm">
      <span className="block font-medium text-slate-700 mb-1">{label}</span>
      {children}
    </label>
  );
}

function Toggle({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
        className="w-4 h-4 accent-indigo-600"
      />
      {label}
    </label>
  );
}
