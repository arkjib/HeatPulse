import { LayoutDashboard, History, Bell, Map as MapIcon, Info, Activity } from 'lucide-react';

export function Sidebar({ activeTab, setActiveTab }: { activeTab: string, setActiveTab: (t: string) => void }) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'history', label: 'History', icon: History },
    { id: 'alerts', label: 'Alerts', icon: Bell },
    { id: 'map', label: 'Map', icon: MapIcon },
    { id: 'about', label: 'About HeatPulse', icon: Info },
  ];

  return (
    <aside className="hidden md:flex flex-col w-64 bg-white border-r border-slate-200 h-screen sticky top-0 shrink-0 z-20">
      <div className="p-6 pt-8">
        <h1 className="text-2xl font-black text-slate-800 flex items-center gap-2">
          <Activity className="h-7 w-7 text-green-600" />
          HeatPulse
        </h1>
        <p className="text-xs text-slate-500 font-semibold mt-1">Extreme Heat. Early Warning.</p>
      </div>

      <nav className="flex-1 px-4 space-y-2 mt-4">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={"w-full flex items-center gap-3 px-4 py-3 rounded-lg font-semibold transition-colors " + (
              activeTab === tab.id 
                ? 'bg-green-700 text-white shadow-sm' 
                : 'text-slate-600 hover:bg-slate-50 hover:text-green-700'
            )}
          >
            <tab.icon className="h-5 w-5" />
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="p-5 m-4 bg-green-50 rounded-xl border border-green-100">
        <h3 className="font-bold text-green-800 text-sm mb-2">About HeatPulse</h3>
        <p className="text-xs text-green-700 leading-relaxed font-medium">
          AI-powered early warning system for extreme heatwaves and human thermal stress.
        </p>
      </div>
    </aside>
  );
}
