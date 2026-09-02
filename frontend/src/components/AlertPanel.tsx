import React from 'react';
import { AlertTriangle, ShieldAlert } from 'lucide-react';
import clsx from 'clsx';

interface AlertPanelProps {
  level: string;
  message: string;
  colorClass: string;
  location: string;
  horizon: number;
}

export const AlertPanel: React.FC<AlertPanelProps> = ({ level, message, colorClass, location, horizon }) => {
  const isExtreme = level === 'EXTREME' || level === 'SEVERE';
  
  return (
    <div className={clsx("rounded-xl p-6 h-full flex flex-col justify-center border", colorClass, isExtreme ? "border-red-900 shadow-md" : "border-transparent")}>
      <div className="flex items-start gap-4">
        <div className={clsx("p-3 rounded-full bg-white/20", isExtreme ? "animate-pulse" : "")}>
          {isExtreme ? <ShieldAlert className="h-8 w-8" /> : <AlertTriangle className="h-8 w-8" />}
        </div>
        <div>
          <h2 className="text-sm font-bold tracking-widest uppercase opacity-80 mb-1">
            Overall Heat Risk • +{horizon}h Forecast
          </h2>
          <div className="text-2xl font-black tracking-tight mb-2 uppercase">
            {level}
          </div>
          <p className="text-base font-medium opacity-90">
            {message}
          </p>
          <div className="mt-3 inline-block px-3 py-1 bg-black/10 rounded-md text-xs font-semibold">
            Location: {location}
          </div>
        </div>
      </div>
    </div>
  );
};
