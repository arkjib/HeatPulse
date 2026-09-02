import React, { useState } from 'react';
import { Search, MapPin, RefreshCw, Activity } from 'lucide-react';
import { format } from 'date-fns';

interface HeaderProps {
  onSearch: (query: string) => void;
  currentLocation: string;
  lat: number;
  lon: number;
  lastUpdated: Date | null;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onSearch, currentLocation, lat, lon, lastUpdated, onRefresh }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) onSearch(query);
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">HeatPulse</h1>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Extreme Heatwave Early Warning</p>
            </div>
          </div>

          <div className="flex flex-col md:flex-row items-center gap-6">
            
            <div className="flex flex-col md:items-end text-sm text-slate-600">
              <div className="flex items-center gap-1 font-semibold text-slate-800">
                <MapPin className="h-4 w-4 text-blue-500" />
                {currentLocation}
              </div>
              <div className="text-xs text-slate-500">
                {lat.toFixed(4)}° N, {lon.toFixed(4)}° E
              </div>
              {lastUpdated && (
                <div className="text-xs mt-1 text-slate-400">
                  Updated: {format(lastUpdated, 'HH:mm')} • Source: Open-Meteo
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto">
              <form onSubmit={handleSubmit} className="relative w-full md:w-64">
                <input 
                  type="text"
                  placeholder="Search location..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-100 border-transparent rounded-lg text-sm focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all"
                />
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              </form>
              
              <button 
                onClick={onRefresh}
                className="p-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-slate-600 transition-colors"
                title="Refresh Forecast"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
          </div>

        </div>
      </div>
    </header>
  );
};
