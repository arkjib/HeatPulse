import type { CurrentWeather as WeatherType } from '../services/api';
import { Thermometer, Droplets, Wind, Gauge, Sun } from 'lucide-react';

export function CurrentWeather({ weather }: { weather?: WeatherType }) {
  if (!weather) return null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col">
      <h2 className="text-lg font-bold text-slate-800 mb-1">Current Weather</h2>
      <p className="text-xs text-slate-500 font-medium mb-5">(Input to Model)</p>
      
      <div className="space-y-4 flex-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-slate-600">
            <Thermometer className="h-5 w-5" />
            <span className="text-sm font-medium">Temperature (2m)</span>
          </div>
          <span className="text-sm font-semibold text-slate-800">{weather.temp_c?.toFixed(1) || '--'} °C</span>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-slate-600">
            <Droplets className="h-5 w-5 text-blue-500" />
            <span className="text-sm font-medium">Relative Humidity</span>
          </div>
          <span className="text-sm font-semibold text-slate-800">{weather.rh_pct?.toFixed(0) || '--'} %</span>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-slate-600">
            <Wind className="h-5 w-5 text-slate-400" />
            <span className="text-sm font-medium">Wind Speed (10m)</span>
          </div>
          <span className="text-sm font-semibold text-slate-800">{weather.wind_ms?.toFixed(1) || '--'} m/s</span>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-slate-600">
            <Gauge className="h-5 w-5 text-slate-500" />
            <span className="text-sm font-medium">Pressure</span>
          </div>
          <span className="text-sm font-semibold text-slate-800">{weather.pressure_hpa?.toFixed(0) || '--'} hPa</span>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-slate-600">
            <Sun className="h-5 w-5 text-yellow-500" />
            <span className="text-sm font-medium">Shortwave Radiation</span>
          </div>
          <span className="text-sm font-semibold text-slate-800">{weather.ghi_wm2?.toFixed(0) || '--'} W/m²</span>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-slate-100">
        <p className="text-xs text-slate-400 font-medium">Source: Open-Meteo</p>
      </div>
    </div>
  );
}
