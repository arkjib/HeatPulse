import React from 'react';
import type { ForecastResponse } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ForecastChartProps {
  sequence: ForecastResponse[];
}

export const ForecastChart: React.FC<ForecastChartProps> = ({ sequence }) => {
  const chartData = [{ name: 'Now', wbgt: sequence[0]?.prediction.wbgt.value, utci: sequence[0]?.prediction.utci.value, hi: sequence[0]?.prediction.hi.value, wbgtRisk: sequence[0]?.risk.wbgt.category, utciRisk: sequence[0]?.risk.utci.category, hiRisk: sequence[0]?.risk.hi.category }];
  
  sequence
    .sort((a, b) => a.forecast_horizon_hours - b.forecast_horizon_hours)
    .forEach(point => {
      chartData.push({
        name: `+${point.forecast_horizon_hours}h`,
        wbgt: point.prediction.wbgt.value,
        utci: point.prediction.utci.value,
        hi: point.prediction.hi.value,
        wbgtRisk: point.risk.wbgt.category,
        utciRisk: point.risk.utci.category,
        hiRisk: point.risk.hi.category,
      });
    });

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-slate-200 shadow-xl rounded-lg text-sm">
          <p className="font-bold text-slate-800 mb-2 border-b pb-2 text-xs uppercase tracking-wider">Time: {label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-6 py-1.5">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
                <span className="font-semibold text-slate-600">{entry.name}:</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-black text-slate-900">{entry.value.toFixed(1)}°C</span>
                <span className="text-[10px] uppercase px-1.5 py-0.5 rounded border border-slate-200 text-slate-500 font-bold w-20 text-center">
                  {entry.payload[`${entry.dataKey}Risk`].replace('_', ' ')}
                </span>
              </div>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-[280px] w-full mt-2">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 10, left: -20, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
          <XAxis 
            dataKey="name" 
            tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 600 }}
            axisLine={{ stroke: '#e2e8f0' }}
            tickLine={false}
            dy={10}
          />
          <YAxis 
            tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 600 }}
            axisLine={false}
            tickLine={false}
            dx={-10}
            unit="°"
          />
          <Tooltip content={<CustomTooltip />} />
          
          <Line 
            type="monotone" 
            dataKey="wbgt" 
            name="WBGT" 
            stroke="#15803d" 
            strokeWidth={3} 
            dot={{ r: 3, strokeWidth: 2, fill: '#fff' }}
            activeDot={{ r: 6 }} 
          />
          <Line 
            type="monotone" 
            dataKey="utci" 
            name="UTCI" 
            stroke="#ea580c" 
            strokeWidth={3}
            dot={{ r: 3, strokeWidth: 2, fill: '#fff' }} 
            activeDot={{ r: 6 }} 
          />
          <Line 
            type="monotone" 
            dataKey="hi" 
            name="HI" 
            stroke="#eab308" 
            strokeWidth={3}
            dot={{ r: 3, strokeWidth: 2, fill: '#fff' }} 
            activeDot={{ r: 6 }} 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
