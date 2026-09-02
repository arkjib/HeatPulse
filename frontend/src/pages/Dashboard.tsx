
import { ThermalCard } from '../components/ThermalCard';
import { ForecastChart } from '../components/ForecastChart';
import { RiskTimeline } from '../components/RiskTimeline';
import { OverallRisk } from '../components/OverallRisk';
import { HeatwaveAlert } from '../components/HeatwaveAlert';
import { CurrentWeather } from '../components/CurrentWeather';
import { ModelInfo } from '../components/ModelInfo';
import { HowItWorks } from '../components/HowItWorks';
import type { ForecastResponse } from '../services/api';

interface DashboardProps {
  sequence: ForecastResponse[];
}

export function Dashboard({ sequence }: DashboardProps) {
  // Default to 72h horizon as shown in the mockup
  const horizon = 72;
  
  const currentForecast = sequence.find(f => f.forecast_horizon_hours === horizon) || sequence[0];

  const getOverallRisk = () => {
    if (!currentForecast) return { level: 'UNKNOWN', text: 'Waiting for data', index: 'N/A' };
    
    const risks = [
      { id: 'WBGT', cat: currentForecast.risk.wbgt.category },
      { id: 'UTCI', cat: currentForecast.risk.utci.category },
      { id: 'Heat Index', cat: currentForecast.risk.hi.category }
    ];
    
    // Sort risks by severity to find dominant
    const riskLevels = ['LOW', 'CAUTION', 'MODERATE', 'STRONG', 'HIGH', 'VERY_HIGH', 'EXTREME', 'EXTREME_DANGER', 'DANGER'];
    
    let highestIndex = -1;
    let dominant = 'WBGT';
    
    risks.forEach(r => {
      const idx = riskLevels.findIndex(l => r.cat.includes(l));
      if (idx > highestIndex) {
        highestIndex = idx;
        dominant = r.id;
      }
    });

    const highestCat = highestIndex >= 0 ? riskLevels[highestIndex] : 'LOW';

    if (highestCat.includes('EXTREME') || highestCat.includes('DANGER')) return { level: 'EXTREME', text: 'Critical heat stress danger. Cancel outdoor activities.', index: dominant };
    if (highestCat.includes('HIGH') || highestCat.includes('STRONG') || highestCat.includes('VERY')) return { level: 'STRONG', text: 'Strong heat stress expected.', index: dominant };
    if (highestCat.includes('MODERATE') || highestCat.includes('CAUTION')) return { level: 'CAUTION', text: 'Caution: fatigue possible with exposure.', index: dominant };
    
    return { level: 'LOW', text: 'Normal conditions. Minimal heat stress.', index: dominant };
  };

  const overallRisk = getOverallRisk();

  if (!sequence.length) return null;

  return (
    <div className="space-y-6">
      {/* Greeting and Overall Risk Row */}
      <div className="flex flex-col md:flex-row gap-6">
        <div className="flex-1 flex flex-col justify-center">
          <h2 className="text-3xl font-black text-slate-800">Welcome back!</h2>
          <p className="text-slate-600 font-medium mt-2">Stay informed. Stay safe.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Main Column (3/4 width on desktop) */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* Thermal Cards */}
          {currentForecast && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <ThermalCard 
                title="WBGT" 
                data={currentForecast.prediction.wbgt}
                risk={currentForecast.risk.wbgt}
              />
              <ThermalCard 
                title="UTCI" 
                data={currentForecast.prediction.utci}
                risk={currentForecast.risk.utci}
              />
              <ThermalCard 
                title="Heat Index" 
                data={currentForecast.prediction.hi}
                risk={currentForecast.risk.hi}
              />
            </div>
          )}

          {/* Chart and Timeline */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-bold text-slate-800">Forecast <span className="font-medium text-slate-500">(Next 120 Hours)</span></h2>
                <div className="flex gap-2">
                  <div className="flex items-center gap-1 text-xs font-bold text-green-700 bg-green-50 px-2 py-1 rounded"><div className="w-2 h-1 bg-green-700"></div> WBGT</div>
                  <div className="flex items-center gap-1 text-xs font-bold text-orange-600 bg-orange-50 px-2 py-1 rounded"><div className="w-2 h-1 bg-orange-600"></div> UTCI</div>
                  <div className="flex items-center gap-1 text-xs font-bold text-yellow-600 bg-yellow-50 px-2 py-1 rounded"><div className="w-2 h-1 bg-yellow-500"></div> HI</div>
                </div>
              </div>
              <ForecastChart sequence={sequence} />
              <p className="text-[10px] text-slate-400 mt-4">All times in local time • Smooth lines show hourly forecast</p>
            </div>
            
            <div className="lg:col-span-1">
              <RiskTimeline sequence={sequence} />
            </div>
          </div>

          <HeatwaveAlert sequence={sequence} />
          
          <HowItWorks />
        </div>

        {/* Right Sidebar (1/4 width on desktop) */}
        <div className="lg:col-span-1 space-y-6">
          <OverallRisk level={overallRisk.level} message={overallRisk.text} dominantIndex={overallRisk.index} />
          <CurrentWeather weather={currentForecast.current_weather} />
          <ModelInfo scope={currentForecast.model_scope} />
        </div>

      </div>
    </div>
  );
}
