import { useState } from 'react';
import { MapPin, Search, RefreshCw, Sun } from 'lucide-react';

interface TopHeaderProps {
  locationName: string;
  onSearch: (query: string) => void;
  onRefresh: () => void;
  lastUpdated: Date | null;
}

export function TopHeader({ locationName, onSearch, onRefresh, lastUpdated }: TopHeaderProps) {
  const [query, setQuery] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
      setIsEditing(false);
    }
  };

  return (
    <div className="relative w-full h-40 bg-slate-900 overflow-hidden shrink-0 shadow-md">
      {/* Spline Background */}
      <iframe 
        src="https://my.spline.design/earthdayandnight-69HuPQYavcBmtugnKqtQeYIs/" 
        frameBorder="0" 
        width="100%" 
        height="100%" 
        className="absolute inset-0 z-0 pointer-events-none opacity-90 scale-150 origin-bottom"
        title="Earth Background"
        loading="lazy"
      ></iframe>
      
      {/* Overlay to ensure text readability */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-900/60 to-slate-900/10 z-0"></div>
      
      {/* Content */}
      <div className="absolute inset-0 z-10 flex items-start justify-between p-6">
        
        {/* Location Selector */}
        <div className="bg-white/95 backdrop-blur-sm shadow-lg rounded-xl p-3 flex flex-col min-w-[280px]">
          {isEditing ? (
            <form onSubmit={handleSubmit} className="flex items-center gap-2">
              <input 
                type="text"
                autoFocus
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search location..."
                className="flex-1 bg-slate-100 px-3 py-2 rounded-lg text-sm font-medium outline-none border border-slate-200 focus:border-green-500"
              />
              <button type="submit" className="bg-green-600 text-white p-2 rounded-lg hover:bg-green-700">
                <Search className="h-4 w-4" />
              </button>
            </form>
          ) : (
            <div 
              className="flex items-center justify-between cursor-pointer group"
              onClick={() => setIsEditing(true)}
            >
              <div className="flex items-center gap-3">
                <div className="bg-green-100 p-2 rounded-full text-green-700">
                  <MapPin className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="font-bold text-slate-800 text-base group-hover:text-green-700 transition-colors">{locationName}</h2>
                </div>
              </div>
              <Search className="h-4 w-4 text-slate-400 group-hover:text-green-600" />
            </div>
          )}
        </div>

        {/* Time and Refresh */}
        <div className="flex flex-col items-end gap-3 text-white">
          <div className="flex items-center gap-4 text-right">
            <div className="flex items-center gap-2">
              <Sun className="h-6 w-6 text-yellow-400" />
              <div>
                <div className="font-bold text-lg leading-none">Day</div>
                <div className="text-xs text-slate-200 mt-1">
                  {lastUpdated ? lastUpdated.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '--:--'}
                </div>
              </div>
            </div>
          </div>
          <button 
            onClick={onRefresh}
            className="flex items-center gap-2 bg-green-600/90 hover:bg-green-600 backdrop-blur-md px-4 py-2 rounded-lg font-semibold text-sm transition-colors shadow-lg"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>

      </div>
    </div>
  );
}
