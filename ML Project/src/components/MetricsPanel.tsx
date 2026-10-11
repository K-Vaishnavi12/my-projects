import { BarChart3, BrainCircuit, Target } from 'lucide-react';
import type { ModelMetrics } from '../types';

interface Props {
  metrics: ModelMetrics;
}

export function MetricsPanel({ metrics }: Props) {
  const clf = metrics.classifier?.xgb_calibrated;
  const base = metrics.classifier?.logreg_baseline;
  const reg = metrics.regressor;

  return (
    <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2 mb-4">
        <BrainCircuit className="w-4 h-4 text-indigo-600" /> Model performance (held-out test set)
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card
          icon={<Target className="w-4 h-4" />}
          title="Cancellation classifier"
          subtitle="XGBoost + isotonic calibration"
          rows={
            clf
              ? [
                  ['ROC-AUC', clf.roc_auc.toFixed(3)],
                  ['PR-AUC', clf.pr_auc.toFixed(3)],
                  ['Brier', clf.brier.toFixed(3)],
                  ['F1 (tuned thr)', clf.f1.toFixed(3)],
                  ['Threshold', clf.threshold.toFixed(3)],
                ]
              : []
          }
          baseline={base ? `LogReg baseline ROC-AUC: ${base.roc_auc.toFixed(3)}` : undefined}
        />
        <Card
          icon={<BarChart3 className="w-4 h-4" />}
          title="Wait-time regressor"
          subtitle="LightGBM quantile loss x 3"
          rows={
            reg
              ? [
                  ['MAE (P50)', `${reg.mae_p50.toFixed(2)} min`],
                  ['RMSE (P50)', `${reg.rmse_p50.toFixed(2)} min`],
                  ['Pinball P10', reg.pinball_p10.toFixed(3)],
                  ['Pinball P50', reg.pinball_p50.toFixed(3)],
                  ['Pinball P90', reg.pinball_p90.toFixed(3)],
                ]
              : []
          }
          baseline={
            reg
              ? `[P10,P90] coverage: ${(reg.coverage_80pct_interval * 100).toFixed(1)}% (target 80%)`
              : undefined
          }
        />
        <Card
          icon={<Target className="w-4 h-4" />}
          title="System design"
          subtitle="What makes this honest"
          rows={[
            ['Split', 'Temporal (last 20%)'],
            ['Calibration', 'Isotonic, 3-fold CV'],
            ['Threshold', 'F1-max from PR curve'],
            ['Quantiles', 'Loss-based, not bootstrap'],
            ['Recommender', 'Counterfactual scoring'],
          ]}
        />
      </div>
    </section>
  );
}

function Card({
  icon,
  title,
  subtitle,
  rows,
  baseline,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  rows: [string, string][];
  baseline?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 p-4 bg-slate-50/50">
      <div className="flex items-center gap-2 text-slate-700 font-medium">
        {icon} {title}
      </div>
      <p className="text-xs text-slate-500 mb-3">{subtitle}</p>
      <dl className="space-y-1">
        {rows.map(([k, v]) => (
          <div key={k} className="flex items-center justify-between text-sm">
            <dt className="text-slate-500">{k}</dt>
            <dd className="font-mono text-slate-800">{v}</dd>
          </div>
        ))}
      </dl>
      {baseline && (
        <p className="text-xs text-slate-500 mt-3 italic border-t border-slate-200 pt-2">
          {baseline}
        </p>
      )}
    </div>
  );
}
