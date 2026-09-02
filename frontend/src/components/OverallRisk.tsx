interface OverallRiskProps {
  level: string;
  message: string;
  dominantIndex: string;
}

export function OverallRisk({ level, message, dominantIndex }: OverallRiskProps) {
  const getRiskColor = (cat: string) => {
    if (cat.includes('EXTREME') || cat.includes('DANGER')) return 'bg-red-600 text-white';
    if (cat.includes('HIGH') || cat.includes('STRONG') || cat.includes('SEVERE')) return 'bg-orange-500 text-white';
    if (cat.includes('MODERATE') || cat.includes('CAUTION')) return 'bg-yellow-400 text-slate-900';
    return 'bg-green-500 text-white';
  };

  const bgClass = getRiskColor(level);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-center h-full">
      <h2 className="text-lg font-bold text-slate-800 mb-4">Overall Heat Risk</h2>
      
      <div className={"w-full py-3 rounded-lg flex items-center justify-center font-black text-xl tracking-wider uppercase mb-4 shadow-sm " + bgClass}>
        {level}
      </div>
      
      <p className="text-slate-700 font-medium text-sm mb-4 leading-relaxed">
        {message}
      </p>

      <div className="bg-orange-50 p-3 rounded-lg border border-orange-100 mt-auto">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold text-orange-800">Driving Index:</span>
          <span className="text-xs font-black text-orange-900 bg-orange-200 px-2 py-0.5 rounded">{dominantIndex}</span>
        </div>
        <p className="text-xs text-orange-800 font-medium">
          Stay hydrated and avoid prolonged outdoor exposure.
        </p>
      </div>
    </div>
  );
}
