import { Pencil, Plus, Trash2, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api';
import type { PatientCreate, PatientOut } from '../types';

const empty: PatientCreate = {
  full_name: '',
  age: 30,
  sex: 'F',
  email: '',
  phone: '',
  has_insurance: true,
  prior_visits: 0,
  prior_no_shows: 0,
  sms_reminder: true,
};

export function PatientsPage() {
  const [rows, setRows] = useState<PatientOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<PatientOut | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<PatientCreate>(empty);

  const refresh = async () => {
    setLoading(true);
    try {
      setRows(await api.listPatients());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm(empty);
    setShowForm(true);
  };

  const openEdit = (p: PatientOut) => {
    setEditing(p);
    setForm({
      full_name: p.full_name,
      age: p.age,
      sex: p.sex,
      email: p.email ?? '',
      phone: p.phone ?? '',
      has_insurance: p.has_insurance,
      prior_visits: p.prior_visits,
      prior_no_shows: p.prior_no_shows,
      sms_reminder: p.sms_reminder,
    });
    setShowForm(true);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      if (editing) await api.updatePatient(editing.id, form);
      else await api.createPatient(form);
      setShowForm(false);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const remove = async (p: PatientOut) => {
    if (!confirm(`Delete patient "${p.full_name}"? This cascades to appointments.`)) return;
    try {
      await api.deletePatient(p.id);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Patients</h2>
          <p className="text-sm text-slate-500">
            Stored in the <code>patients</code> table.
          </p>
        </div>
        <button className="btn-primary" onClick={openCreate}>
          <Plus className="w-4 h-4" /> New patient
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
              <th className="text-left px-4 py-2">Name</th>
              <th className="text-left px-4 py-2">Age</th>
              <th className="text-left px-4 py-2">Sex</th>
              <th className="text-left px-4 py-2">Ins.</th>
              <th className="text-left px-4 py-2">Visits</th>
              <th className="text-left px-4 py-2">No-shows</th>
              <th className="text-left px-4 py-2">SMS</th>
              <th className="text-right px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={9} className="text-center py-6 text-slate-500">
                  Loading...
                </td>
              </tr>
            )}
            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={9} className="text-center py-6 text-slate-500">
                  No patients yet. Create one.
                </td>
              </tr>
            )}
            {rows.map((p) => (
              <tr key={p.id} className="border-t border-slate-100">
                <td className="px-4 py-2 font-mono text-slate-500">{p.id}</td>
                <td className="px-4 py-2 font-medium text-slate-800">{p.full_name}</td>
                <td className="px-4 py-2">{p.age}</td>
                <td className="px-4 py-2">{p.sex}</td>
                <td className="px-4 py-2">{p.has_insurance ? 'yes' : 'no'}</td>
                <td className="px-4 py-2">{p.prior_visits}</td>
                <td className="px-4 py-2">{p.prior_no_shows}</td>
                <td className="px-4 py-2">{p.sms_reminder ? 'yes' : 'no'}</td>
                <td className="px-4 py-2 text-right">
                  <button
                    className="inline-flex items-center gap-1 text-slate-600 hover:text-indigo-600 px-2"
                    onClick={() => openEdit(p)}
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    className="inline-flex items-center gap-1 text-slate-600 hover:text-rose-600 px-2"
                    onClick={() => remove(p)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
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
              <h3 className="text-lg font-semibold">
                {editing ? `Edit patient #${editing.id}` : 'New patient'}
              </h3>
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
                <span className="block font-medium mb-1">Full name</span>
                <input
                  className="input"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  required
                />
              </label>
              <label className="text-sm">
                <span className="block font-medium mb-1">Age</span>
                <input
                  className="input"
                  type="number"
                  min={0}
                  max={120}
                  value={form.age}
                  onChange={(e) => setForm({ ...form, age: parseInt(e.target.value || '0', 10) })}
                />
              </label>
              <label className="text-sm">
                <span className="block font-medium mb-1">Sex</span>
                <select
                  className="select"
                  value={form.sex}
                  onChange={(e) => setForm({ ...form, sex: e.target.value })}
                >
                  <option value="F">F</option>
                  <option value="M">M</option>
                  <option value="O">O</option>
                </select>
              </label>
              <label className="text-sm">
                <span className="block font-medium mb-1">Prior visits</span>
                <input
                  className="input"
                  type="number"
                  min={0}
                  value={form.prior_visits}
                  onChange={(e) =>
                    setForm({ ...form, prior_visits: parseInt(e.target.value || '0', 10) })
                  }
                />
              </label>
              <label className="text-sm">
                <span className="block font-medium mb-1">Prior no-shows</span>
                <input
                  className="input"
                  type="number"
                  min={0}
                  value={form.prior_no_shows}
                  onChange={(e) =>
                    setForm({ ...form, prior_no_shows: parseInt(e.target.value || '0', 10) })
                  }
                />
              </label>
              <label className="text-sm">
                <span className="block font-medium mb-1">Email</span>
                <input
                  className="input"
                  type="email"
                  value={form.email ?? ''}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </label>
              <label className="text-sm">
                <span className="block font-medium mb-1">Phone</span>
                <input
                  className="input"
                  value={form.phone ?? ''}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                />
              </label>
            </div>

            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  className="w-4 h-4 accent-indigo-600"
                  checked={form.has_insurance}
                  onChange={(e) => setForm({ ...form, has_insurance: e.target.checked })}
                />
                Has insurance
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  className="w-4 h-4 accent-indigo-600"
                  checked={form.sms_reminder}
                  onChange={(e) => setForm({ ...form, sms_reminder: e.target.checked })}
                />
                SMS reminder
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                Cancel
              </button>
              <button type="submit" className="btn-primary">
                {editing ? 'Save changes' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
