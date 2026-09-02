import { ShieldCheck, AlertTriangle } from 'lucide-react';
import type { ForecastResponse } from '../services/api';

export function HeatwaveAlert({ sequence }: { sequence: ForecastResponse[] }) {
  const getOverallRisk = (f: ForecastResponse) => {
    const risks = [f.risk.wbgt.category, f.risk.utci.category, f.risk.hi.category];
    if (risks.includes('EXTREME_DANGER') || risks.includes('EXTREME')) return { level: 'EXTREME', val: 4 };
    if (risks.includes('DANGER') || risks.includes('VERY_HIGH') || risks.includes('VERY_STRONG') || risks.includes('HIGH') || risks.includes('STRONG') || risks.includes('EXTREME_CAUTION')) return { level: 'STRONG', val: 3 };
    if (risks.includes('MODERATE') || risks.includes('CAUTION')) return { level: 'CAUTION', val: 2 };
    return { level: 'LOW', val: 1 };
  };

  if (!sequence.length) return null;

  let peak = { level: 'LOW', val: 1, hour: 0 };
  sequence.forEach(f => {
    const r = getOverallRisk(f);
    if (r.val > peak.val) {
      peak = { ...r, hour: f.forecast_horizon_hours };
    }
  });

  const isSafe = peak.val === 1;

  return (
    <div className={"rounded-xl shadow-sm border p-6 flex flex-col md:flex-row md:items-center justify-between gap-6 " + (isSafe ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200')}>
      <div className="flex items-start gap-4">
        <div className={"p-3 rounded-full " + (isSafe ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600')}>
          {isSafe ? <ShieldCheck className="h-8 w-8" /> : <AlertTriangle className="h-8 w-8" />}
        </div>
        <div>
          <h2 className="text-sm font-bold text-slate-800 mb-1">Heatwave Alert</h2>
          <h3 className={"text-lg font-black mb-1 " + (isSafe ? 'text-green-700' : 'text-red-700')}>
            {isSafe ? 'No Significant Heat Risk' : 'Heat Risk Active'}
          </h3>
          <p className="text-sm text-slate-600 font-medium">
            {isSafe ? 'No heatwave conditions expected in the next 120 hours.' : 'Please take precautions during peak hours.'}
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex justify-between items-center gap-6">
          <span className="text-sm font-medium text-slate-500 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" /> Peak Risk:
          </span>
          <span className={"font-black uppercase " + (isSafe ? 'text-green-600' : 'text-red-600')}>{peak.level}</span>
        </div>
        <div className="flex justify-between items-center gap-6">
          <span className="text-sm font-medium text-slate-500 flex items-center gap-2">
            <ShieldCheck className="h-4 w-4" /> Expected:
          </span>
          <span className="text-sm font-bold text-slate-700">{peak.hour > 0 ? (peak.hour - 24 > 0 ? peak.hour - 24 : 0) + 'h - ' + peak.hour + 'h' : '--'}</span>
        </div>
      </div>
    </div>
  );
}
