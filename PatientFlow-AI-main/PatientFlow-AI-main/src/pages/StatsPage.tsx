import { useEffect, useState } from 'react';
import { api } from '../api';
import type { StatsResponse } from '../types';

export function StatsPage() {
  const [data, setData] = useState<StatsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.stats().then(setData).catch((e) => setError((e as Error).message));
  }, []);

  if (error)
    return (
      <div className="rounded-xl bg-rose-50 border border-rose-200 text-rose-800 p-3 text-sm">
        {error}
      </div>
    );
  if (!data) return <div className="text-slate-500">Loading stats from SQL...</div>;

  const { totals, appointments_by_status, doctor_load, revenue_by_type, top_no_show_patients } = data;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Analytics</h2>
        <p className="text-sm text-slate-500">
          All numbers computed via SQL <code>GROUP BY</code> queries against the database.
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <Kpi label="Patients" value={totals.patients} />
        <Kpi label="Appointments" value={totals.appointments} />
        <Kpi label="Doctors" value={totals.doctors} />
        <Kpi label="Invoices" value={totals.invoices} />
        <Kpi label="Revenue (paid)" value={`INR ${totals.revenue_paid.toFixed(0)}`} accent="emerald" />
        <Kpi label="Revenue (pending)" value={`INR ${totals.revenue_pending.toFixed(0)}`} accent="amber" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Appointments by status">
          <SimpleTable
            columns={['Status', 'Count']}
            rows={appointments_by_status.map((r) => [r.status, r.count])}
          />
        </Card>

        <Card title="Revenue by appointment type">
          <SimpleTable
            columns={['Type', 'Invoices', 'Total (INR)']}
            rows={revenue_by_type.map((r) => [
              r.appointment_type_id,
              r.invoices,
              r.total_amount.toFixed(2),
            ])}
          />
        </Card>

        <Card title="Doctor load">
          <SimpleTable
            columns={['Doctor', 'Total', 'Done', 'Canc.', 'No-show']}
            rows={doctor_load.map((r) => [
              r.doctor_id.split('_').slice(2).join(' ') + ` (${r.specialty})`,
              r.total,
              r.completed,
              r.cancelled,
              r.no_show,
            ])}
          />
        </Card>

        <Card title="Top no-show patients">
          {top_no_show_patients.length === 0 ? (
            <p className="text-sm text-slate-500">No no-shows observed yet.</p>
          ) : (
            <SimpleTable
              columns={['ID', 'Name', 'No-shows']}
              rows={top_no_show_patients.map((r) => [r.patient_id, r.full_name, r.no_shows])}
            />
          )}
        </Card>
      </div>
    </div>
  );
}

function Kpi({
  label,
  value,
  accent = 'indigo',
}: {
  label: string;
  value: number | string;
  accent?: 'indigo' | 'emerald' | 'amber';
}) {
  const color =
    accent === 'emerald'
      ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
      : accent === 'amber'
      ? 'text-amber-700 bg-amber-50 border-amber-200'
      : 'text-indigo-700 bg-indigo-50 border-indigo-200';
  return (
    <div className={`rounded-xl border p-3 ${color}`}>
      <div className="text-xs uppercase tracking-wide opacity-80">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 space-y-3">
      <h3 className="font-semibold text-slate-800">{title}</h3>
      {children}
    </div>
  );
}

function SimpleTable({
  columns,
  rows,
}: {
  columns: string[];
  rows: (string | number)[][];
}) {
  return (
    <table className="w-full text-sm">
      <thead className="text-slate-500">
        <tr>
          {columns.map((c) => (
            <th key={c} className="text-left py-1 pr-2 font-medium">
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td colSpan={columns.length} className="text-slate-400 py-2">
              -
            </td>
          </tr>
        )}
        {rows.map((r, i) => (
          <tr key={i} className="border-t border-slate-100">
            {r.map((c, j) => (
              <td key={j} className="py-1 pr-2 text-slate-700">
                {c}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
