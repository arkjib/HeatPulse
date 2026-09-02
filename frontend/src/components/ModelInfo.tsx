import { Info } from 'lucide-react';
import type { ModelScope } from '../services/api';

export function ModelInfo({ scope }: { scope?: ModelScope }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-lg font-bold text-slate-800 mb-6">Model Information</h2>
      
      <div className="space-y-4">
        <div className="flex justify-between items-start border-b border-slate-100 pb-3">
          <span className="text-sm font-medium text-slate-500">Models</span>
          <span className="text-sm font-semibold text-slate-800 text-right">Ridge, Random Forest</span>
        </div>
        <div className="flex justify-between items-start border-b border-slate-100 pb-3">
          <span className="text-sm font-medium text-slate-500">Forecast Horizons</span>
          <span className="text-sm font-semibold text-slate-800 text-right">24h, 48h, 72h, 96h, 120h</span>
        </div>
        <div className="flex justify-between items-start border-b border-slate-100 pb-3">
          <span className="text-sm font-medium text-slate-500">Indices</span>
          <span className="text-sm font-semibold text-slate-800 text-right">WBGT, UTCI, Heat Index</span>
        </div>
        <div className="flex justify-between items-start border-b border-slate-100 pb-3">
          <span className="text-sm font-medium text-slate-500">Validation Location</span>
          <span className="text-sm font-semibold text-slate-800 text-right">Kochi, India</span>
        </div>
        <div className="flex justify-between items-start border-b border-slate-100 pb-3">
          <span className="text-sm font-medium text-slate-500">Test Period</span>
          <span className="text-sm font-semibold text-slate-800 text-right">08 Feb 2025 - 27 Jun 2026</span>
        </div>
        <div className="flex justify-between items-start">
          <span className="text-sm font-medium text-slate-500">Test Samples</span>
          <span className="text-sm font-semibold text-slate-800 text-right">1,172 observations</span>
        </div>
      </div>

      {scope && (
        <div className={"mt-6 p-4 rounded-xl border flex items-start gap-3 " + 
          (scope.status === 'IN_VALIDATED_REGION' ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200')
        }>
          <Info className={"h-5 w-5 shrink-0 mt-0.5 " + 
            (scope.status === 'IN_VALIDATED_REGION' ? 'text-green-600' : 'text-yellow-600')
          } />
          <p className={"text-xs leading-relaxed font-medium " + 
            (scope.status === 'IN_VALIDATED_REGION' ? 'text-green-800' : 'text-yellow-800')
          }>
            {scope.warning || "These predictions are inside the model's primary validated region."}
          </p>
        </div>
      )}
    </div>
  );
}
