import { Activity, BarChart3, CalendarDays, LineChart, Users, Wifi, WifiOff } from 'lucide-react';
import { useEffect, useState } from 'react';
import { NavLink, Navigate, Route, Routes } from 'react-router-dom';
import { API_BASE, api } from './api';
import { AppointmentsPage } from './pages/AppointmentsPage';
import { PatientsPage } from './pages/PatientsPage';
import { PredictPage } from './pages/PredictPage';
import { StatsPage } from './pages/StatsPage';
import type { MetadataResponse } from './types';

function App() {
  const [meta, setMeta] = useState<MetadataResponse | null>(null);
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [dbHealthy, setDbHealthy] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const h = await api.health();
        const m = await api.metadata();
        if (cancelled) return;
        setHealthy(true);
        setDbHealthy(h.db);
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

  const navLink = (to: string, label: string, Icon: typeof Users) => (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
          isActive
            ? 'bg-indigo-600 text-white'
            : 'text-slate-600 hover:bg-slate-100'
        }`
      }
    >
      <Icon className="w-4 h-4" />
      {label}
    </NavLink>
  );

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white grid place-items-center">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900">PatientFlow AI</h1>
              <p className="text-xs text-slate-500">
                SQL-backed cancellation-risk + wait-time forecasting
              </p>
            </div>
          </div>

          <nav className="flex items-center gap-1">
            {navLink('/patients', 'Patients', Users)}
            {navLink('/appointments', 'Appointments', CalendarDays)}
            {navLink('/stats', 'Stats', BarChart3)}
            {navLink('/predict', 'Predict', LineChart)}
          </nav>

          <div className="flex items-center gap-2 text-xs text-slate-500">
            <code className="px-2 py-1 rounded bg-slate-100 text-slate-700">{API_BASE}</code>
            {healthy === true ? (
              <span className="flex items-center gap-1 text-emerald-600">
                <Wifi className="w-3 h-3" /> api
              </span>
            ) : healthy === false ? (
              <span className="flex items-center gap-1 text-rose-600">
                <WifiOff className="w-3 h-3" /> api
              </span>
            ) : null}
            {dbHealthy === true && (
              <span className="text-emerald-600">db ok</span>
            )}
            {dbHealthy === false && (
              <span className="text-rose-600">db down</span>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6 space-y-6">
        {error && (
          <div className="rounded-xl bg-rose-50 border border-rose-200 text-rose-800 p-4 text-sm">
            <strong>Error:</strong> {error}
            <p className="mt-1 text-xs text-rose-700">
              Make sure the FastAPI backend + MySQL are running.
            </p>
          </div>
        )}

        <Routes>
          <Route path="/" element={<Navigate to="/patients" replace />} />
          <Route path="/patients" element={<PatientsPage />} />
          <Route
            path="/appointments"
            element={
              <AppointmentsPage
                doctors={meta?.doctors ?? []}
                appointmentTypes={meta?.appointment_types ?? []}
              />
            }
          />
          <Route
            path="/predict"
            element={<PredictPage meta={meta} />}
          />
          <Route path="/stats" element={<StatsPage />} />
          <Route path="*" element={<Navigate to="/patients" replace />} />
        </Routes>

        <footer className="text-center text-xs text-slate-400 pt-4">
          MySQL-backed. All predictions and recommendations are logged to the
          <code className="px-1"> predictions </code> and
          <code className="px-1"> recommendation_runs </code> tables.
        </footer>
      </main>
    </div>
  );
}

export default App;
