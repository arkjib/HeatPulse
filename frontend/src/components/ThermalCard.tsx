import { ThermometerSun } from 'lucide-react';
import type { PredictionDetail, RiskResponse } from '../services/api';

interface ThermalCardProps {
  title: string;
  data: PredictionDetail;
  risk: RiskResponse;
}

export function ThermalCard({ title, data, risk }: ThermalCardProps) {
  const getRiskColor = (cat: string) => {
    if (cat.includes('EXTREME') || cat.includes('DANGER')) return 'bg-red-100 text-red-800 border-red-200';
    if (cat.includes('HIGH') || cat.includes('STRONG')) return 'bg-orange-100 text-orange-800 border-orange-200';
    if (cat.includes('MODERATE') || cat.includes('CAUTION')) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    return 'bg-green-100 text-green-800 border-green-200';
  };

  const getIconColor = (cat: string) => {
    if (cat.includes('EXTREME') || cat.includes('DANGER')) return 'text-red-500 bg-red-50';
    if (cat.includes('HIGH') || cat.includes('STRONG')) return 'text-orange-500 bg-orange-50';
    if (cat.includes('MODERATE') || cat.includes('CAUTION')) return 'text-yellow-500 bg-yellow-50';
    return 'text-green-500 bg-green-50';
  };

  const riskCat = risk?.category || 'UNKNOWN';
  const riskColor = getRiskColor(riskCat);
  const iconColor = getIconColor(riskCat);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col h-full hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        <div className={"p-3 rounded-full " + iconColor}>
          <ThermometerSun className="h-8 w-8" />
        </div>
        <div className="flex-1">
          <div className="flex justify-between items-start">
            <h3 className="font-bold text-slate-800 text-lg">{title}</h3>
            <span className={"px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider border " + riskColor}>
              {riskCat.replace('_', ' ')}
            </span>
          </div>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-3xl font-black text-slate-900">{data?.value?.toFixed(2) || '--'}</span>
            <span className="text-lg font-bold text-slate-500">°C</span>
          </div>
          <p className="text-sm font-medium text-slate-700 mt-2 line-clamp-1">{risk?.description || 'No data'}</p>
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t border-slate-100 space-y-1">
        <div className="flex justify-between items-center text-sm">
          <span className="text-slate-500 font-medium">Model:</span>
          <span className="text-slate-800 font-semibold">{data?.model_used || 'Unknown'}</span>
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-slate-500 font-medium">Test RMSE:</span>
          <span className="text-slate-800 font-semibold">{data?.rmse_test_error?.toFixed(3) || 'N/A'} °C</span>
        </div>
      </div>
    </div>
  );
}
