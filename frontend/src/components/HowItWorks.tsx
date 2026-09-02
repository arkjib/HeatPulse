import { Cloud, Clock, ThermometerSun, ListOrdered, BrainCircuit, ShieldCheck } from 'lucide-react';

export function HowItWorks() {
  const steps = [
    { icon: Cloud, title: '1. Live Weather', desc: 'Real-time data from Open-Meteo' },
    { icon: Clock, title: '2. Historical Context', desc: 'Recent history builds the full picture' },
    { icon: ThermometerSun, title: '3. Thermal Physics', desc: 'Calculate WBGT, UTCI & Heat Index' },
    { icon: ListOrdered, title: '4. 90 Engineered Features', desc: 'Lags, rolling stats, trends & more' },
    { icon: BrainCircuit, title: '5. ML Forecasting', desc: 'Ridge & RF models forecast up to 120h' },
    { icon: ShieldCheck, title: '6. Risk Classification', desc: 'Convert forecasts into human risk levels' },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
      <h2 className="text-lg font-bold text-slate-800 mb-6">How HeatPulse Works</h2>
      
      <div className="flex flex-wrap md:flex-nowrap items-start justify-between gap-4">
        {steps.map((step, idx) => (
          <div key={idx} className="flex flex-col flex-1 items-center md:items-start text-center md:text-left">
            <div className="flex items-center gap-3 w-full justify-center md:justify-start">
              <div className="p-3 bg-slate-50 rounded-full text-slate-700 border border-slate-200">
                <step.icon className="h-6 w-6" />
              </div>
              {idx < steps.length - 1 && (
                <div className="hidden md:block flex-1 h-px bg-slate-200 mx-2"></div>
              )}
            </div>
            <h3 className="font-bold text-slate-800 text-xs mt-3">{step.title}</h3>
            <p className="text-[11px] text-slate-500 mt-1 leading-tight">{step.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
