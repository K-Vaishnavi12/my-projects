import { Plus, Sparkles, Trash2, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api';
import type {
  AppointmentCreate,
  AppointmentOut,
  AppointmentTypeMeta,
  DoctorMeta,
  PatientOut,
  PredictResponse,
} from '../types';

interface Props {
  doctors: DoctorMeta[];
  appointmentTypes: AppointmentTypeMeta[];
}

const defaultTime = (): string => {
  const d = new Date();
  d.setDate(d.getDate() + 2);
  d.setHours(10, 0, 0, 0);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours(),
  )}:${pad(d.getMinutes())}`;
};

export function AppointmentsPage({ doctors, appointmentTypes }: Props) {
  const [rows, setRows] = useState<AppointmentOut[]>([]);
  const [patients, setPatients] = useState<PatientOut[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<AppointmentCreate>({
    patient_id: 0,
    doctor_id: '',
    appointment_type_id: '',
    appointment_time: defaultTime(),
    lead_time_days: 2,
    status: 'scheduled',
    notes: '',
  });
  const [busyId, setBusyId] = useState<number | null>(null);
  const [predResult, setPredResult] = useState<Record<number, PredictResponse>>({});

  const refresh = async () => {
    try {
      const [a, p] = await Promise.all([api.listAppointments(), api.listPatients()]);
      setRows(a);
      setPatients(p);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (!form.doctor_id && doctors.length) {
      setForm((f) => ({ ...f, doctor_id: doctors[0].id }));
    }
    if (!form.appointment_type_id && appointmentTypes.length) {
      setForm((f) => ({ ...f, appointment_type_id: appointmentTypes[0].id }));
    }
    if (!form.patient_id && patients.length) {
      setForm((f) => ({ ...f, patient_id: patients[0].id }));
    }
  }, [doctors, appointmentTypes, patients, form.doctor_id, form.appointment_type_id, form.patient_id]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await api.createAppointment(form);
      setShowForm(false);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const remove = async (a: AppointmentOut) => {
    if (!confirm(`Delete appointment #${a.id}?`)) return;
    try {
      await api.deleteAppointment(a.id);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const runPrediction = async (a: AppointmentOut) => {
    const patient = patients.find((p) => p.id === a.patient_id);
    if (!patient) return;
    setBusyId(a.id);
    try {
      const r = await api.predict(
        {
          doctor_id: a.doctor_id,
          appointment_type: a.appointment_type_id,
          appointment_time: a.appointment_time,
          age: patient.age,
          sex: patient.sex,
          has_insurance: patient.has_insurance,
          lead_time_days: a.lead_time_days,
          prior_no_shows: patient.prior_no_shows,
          prior_visits: patient.prior_visits,
          sms_reminder: patient.sms_reminder,
        },
        { patient_id: patient.id, appointment_id: a.id },
      );
      setPredResult({ ...predResult, [a.id]: r });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusyId(null);
    }
  };

  const patientName = (id: number) =>
    patients.find((p) => p.id === id)?.full_name ?? `#${id}`;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Appointments</h2>
          <p className="text-sm text-slate-500">
            Stored in the <code>appointments</code> table. Predictions are saved to{' '}
            <code>predictions</code>.
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => setShowForm(true)}
          disabled={patients.length === 0}
          title={patients.length === 0 ? 'Create a patient first' : undefined}
        >
          <Plus className="w-4 h-4" /> New appointment
        </button>
      </div>

      {error && (
        <div className="rounded-xl bg-rose-50 border border-rose-200 text-rose-800 p-3 text-sm">
          {error}
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="text-left px-4 py-2">ID</th>
              <th className="text-left px-4 py-2">Patient</th>
              <th className="text-left px-4 py-2">Doctor</th>
              <th className="text-left px-4 py-2">Type</th>
              <th className="text-left px-4 py-2">When</th>
              <th className="text-left px-4 py-2">Status</th>
              <th className="text-left px-4 py-2">Prediction</th>
              <th className="text-right px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={8} className="text-center py-6 text-slate-500">
                  No appointments scheduled yet.
                </td>
              </tr>
            )}
            {rows.map((a) => {
              const pred = predResult[a.id];
              return (
                <tr key={a.id} className="border-t border-slate-100">
                  <td className="px-4 py-2 font-mono text-slate-500">{a.id}</td>
                  <td className="px-4 py-2">{patientName(a.patient_id)}</td>
                  <td className="px-4 py-2">{a.doctor_id.split('_').slice(2).join(' ')}</td>
                  <td className="px-4 py-2">{a.appointment_type_id}</td>
                  <td className="px-4 py-2 text-slate-600">
                    {new Date(a.appointment_time).toLocaleString()}
                  </td>
                  <td className="px-4 py-2">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs ${
                        a.status === 'scheduled'
                          ? 'bg-indigo-50 text-indigo-700'
                          : a.status === 'cancelled' || a.status === 'no_show'
                          ? 'bg-rose-50 text-rose-700'
                          : 'bg-emerald-50 text-emerald-700'
                      }`}
                    >
                      {a.status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-xs">
                    {pred ? (
                      <div>
                        <div>
                          cancel: <strong>{(pred.cancellation_prob * 100).toFixed(1)}%</strong>
                        </div>
                        <div className="text-slate-500">
                          wait p50: {pred.expected_wait_minutes.p50.toFixed(1)} min
                        </div>
                      </div>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 px-2 disabled:opacity-40"
                      onClick={() => runPrediction(a)}
                      disabled={busyId === a.id}
                      title="Run + persist prediction"
                    >
                      <Sparkles className="w-4 h-4" />
                    </button>
                    <button
                      className="inline-flex items-center gap-1 text-slate-600 hover:text-rose-600 px-2"
                      onClick={() => remove(a)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-slate-900/40 grid place-items-center p-4 z-50">
          <form
            onSubmit={submit}
            className="bg-white rounded-2xl shadow-lg border border-slate-200 p-6 w-full max-w-lg space-y-4"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">New appointment</h3>
              <button
                type="button"
                className="text-slate-400 hover:text-slate-700"
                onClick={() => setShowForm(false)}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm col-span-2">
                <span className="block font-medium mb-1">Patient</span>
                <select
                  className="select"
                  value={form.patient_id}
                  onChange={(e) => setForm({ ...form, patient_id: parseInt(e.target.value, 10) })}
                  required
                >
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      #{p.id} - {p.full_name} ({p.age}{p.sex})
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm">
                <span className="block font-medium mb-1">Doctor</span>
                <select
                  className="select"
                  value={form.doctor_id}
                  onChange={(e) => setForm({ ...form, doctor_id: e.target.value })}
                >
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.id.split('_').slice(2).join(' ')} - {d.specialty}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm">
                <span className="block font-medium mb-1">Type</span>
                <select
                  className="select"
                  value={form.appointment_type_id}
                  onChange={(e) => setForm({ ...form, appointment_type_id: e.target.value })}
                >
                  {appointmentTypes.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.id.replace('_', ' ')}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm">
                <span className="block font-medium mb-1">When</span>
                <input
                  className="input"
                  type="datetime-local"
                  value={form.appointment_time}
                  onChange={(e) => setForm({ ...form, appointment_time: e.target.value })}
                  required
                />
              </label>
              <label className="text-sm">
                <span className="block font-medium mb-1">Lead time (days)</span>
                <input
                  className="input"
                  type="number"
                  min={0}
                  value={form.lead_time_days}
                  onChange={(e) =>
                    setForm({ ...form, lead_time_days: parseInt(e.target.value || '0', 10) })
                  }
                />
              </label>
              <label className="text-sm col-span-2">
                <span className="block font-medium mb-1">Notes</span>
                <textarea
                  className="input"
                  value={form.notes ?? ''}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  rows={2}
                />
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                Cancel
              </button>
              <button type="submit" className="btn-primary">
                Create
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
