import type { ForecastResponse } from '../services/api';

export function RiskTimeline({ sequence }: { sequence: ForecastResponse[] }) {
  const getRiskColor = (cat: string) => {
    if (cat.includes('EXTREME') || cat.includes('DANGER')) return 'text-red-500 bg-red-500';
    if (cat.includes('HIGH') || cat.includes('STRONG') || cat.includes('SEVERE')) return 'text-orange-500 bg-orange-500';
    if (cat.includes('MODERATE') || cat.includes('CAUTION')) return 'text-yellow-500 bg-yellow-500';
    return 'text-green-500 bg-green-500';
  };

  const getOverallRisk = (f: ForecastResponse) => {
    const risks = [f.risk.wbgt.category, f.risk.utci.category, f.risk.hi.category];
    if (risks.includes('EXTREME_DANGER') || risks.includes('EXTREME')) return 'EXTREME DANGER';
    if (risks.includes('DANGER') || risks.includes('VERY_HIGH') || risks.includes('VERY_STRONG')) return 'SEVERE';
    if (risks.includes('HIGH') || risks.includes('STRONG') || risks.includes('EXTREME_CAUTION')) return 'STRONG';
    if (risks.includes('MODERATE') || risks.includes('CAUTION')) return 'CAUTION';
    return 'LOW';
  };

  const sorted = [...sequence].sort((a, b) => a.forecast_horizon_hours - b.forecast_horizon_hours);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col h-full">
      <h2 className="text-lg font-bold text-slate-800 mb-1">Risk Timeline <span className="text-sm font-medium text-slate-500 font-normal">(Dominant Risk)</span></h2>
      
      <div className="flex-1 overflow-y-auto mt-4 space-y-4">
        {sorted.map((f, i) => {
          const prev = i === 0 ? 0 : sorted[i-1].forecast_horizon_hours;
          const curr = f.forecast_horizon_hours;
          const riskLabel = getOverallRisk(f);
          const color = getRiskColor(riskLabel);
          
          return (
            <div key={f.forecast_horizon_hours} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={"w-2.5 h-2.5 rounded-full " + color.split(' ')[1]}></div>
                <span className={"font-bold text-sm " + color.split(' ')[0]}>{riskLabel}</span>
              </div>
              <span className="text-sm font-medium text-slate-600">
                {prev === 0 ? 'Now' : prev + 'h'} - {curr}h
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-6 pt-4 border-t border-slate-100">
        <p className="text-xs text-slate-400">Tap points on chart for details</p>
      </div>
    </div>
  );
}
