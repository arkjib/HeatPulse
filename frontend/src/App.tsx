// @ts-nocheck
import React, { useState, useEffect } from 'react';
import { 
  Thermometer, Activity, Flame, Droplets, MapPin, Clock, RefreshCw,
  Wind, Sun, CloudRain, CheckCircle, AlertTriangle, AlertOctagon, Info, Layers, ShieldAlert
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { MapContainer, TileLayer, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import LandingPage from './pages/LandingPage';

export default function App() {
  const [showLanding, setShowLanding] = useState(true);
  const [currentData, setCurrentData] = useState(null);
  const [seqData, setSeqData] = useState(null);
  const [wardsData, setWardsData] = useState([]);
  const [riskData, setRiskData] = useState(null);
  const [selectedHorizon, setSelectedHorizon] = useState(72);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState('');
  const [now, setNow] = useState(new Date());

  const LAT = 9.9312;
  const LON = 76.2673;

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [resCurrent, resSeq, resWards, resRisk] = await Promise.all([
        fetch(`/api/v1/thermal/current?lat=${LAT}&lon=${LON}`),
        fetch(`/api/v1/forecast/sequence?latitude=${LAT}&longitude=${LON}`),
        fetch(`/api/v1/wards/weather`),
        fetch(`/api/v1/risk/forecast?lat=${LAT}&lon=${LON}`)
      ]);
      
      const curr = await resCurrent.json();
      const seq = await resSeq.json();
      const wrd = await resWards.json();
      const risk = await resRisk.json();
      
      setCurrentData(curr);
      setSeqData(seq);
      setWardsData(wrd?.wards || []);
      setRiskData(risk);
      setLastUpdated(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    } catch (e) {
      console.error("Failed to fetch data", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  // Compute aggregated risk from sequence
  const targetForecast = Array.isArray(seqData) ? seqData.find(d => d.forecast_horizon_hours === selectedHorizon) : undefined;
  
  // Use authoritative risk model data if available (we assume riskData corresponds to horizons roughly)
  const getRiskForHorizon = (h) => {
      if (!Array.isArray(riskData)) return null;
      const idx = h / 24 - 1;
      return riskData[idx];
  };
  const authoritativeRisk = getRiskForHorizon(selectedHorizon);
  
  // Chart Data preparation
  const chartData = [];
  if (currentData && !currentData.detail) {
    chartData.push({
      name: 'Now',
      fullTime: 'Current Time',
      horizon: 0,
      WBGT: Number(currentData.wbgt?.value_c?.toFixed(1)) || 0,
      UTCI: Number(currentData.utci?.value_c?.toFixed(1)) || 0,
      HeatIndex: Number(currentData.heat_index?.value_c?.toFixed(1)) || 0
    });
  }
  if (Array.isArray(seqData)) {
    seqData.forEach(d => {
      if (d.forecast_horizon_hours <= selectedHorizon) {
        // Convert horizon hours to actual day string
        const fDate = new Date();
        fDate.setHours(fDate.getHours() + d.forecast_horizon_hours);
        const dayName = fDate.toLocaleDateString('en-GB', { weekday: 'short', hour: '2-digit', hour12: true });

        chartData.push({
          name: `+${d.forecast_horizon_hours}h`,
          fullTime: dayName,
          horizon: d.forecast_horizon_hours,
          WBGT: Number(d.prediction?.wbgt?.value?.toFixed(1)) || 0,
          UTCI: Number(d.prediction?.utci?.value?.toFixed(1)) || 0,
          HeatIndex: Number(d.prediction?.hi?.value?.toFixed(1)) || 0
        });
      }
    });
  }

  const getRiskColor = (cat) => {
    switch (cat?.toUpperCase()) {
      case 'LOW':
      case 'SAFE':
      case 'NO THERMAL STRESS':
      case 'NO_THERMAL_STRESS':
      case 'COLD STRESS':
      case 'COLD_STRESS': return 'text-green-400 border-green-400/30 bg-green-400/10';
      case 'CAUTION': return 'text-yellow-400 border-yellow-400/30 bg-yellow-400/10';
      case 'MODERATE': return 'text-amber-400 border-amber-400/30 bg-amber-400/10';
      case 'STRONG':
      case 'HIGH':
      case 'EXTREME CAUTION':
      case 'EXTREME_CAUTION':
      case 'VERY_HIGH': return 'text-orange-500 border-orange-500/30 bg-orange-500/10';
      case 'EXTREME':
      case 'VERY_STRONG':
      case 'VERY STRONG':
      case 'DANGER':
      case 'EXTREME DANGER':
      case 'EXTREME_DANGER': return 'text-red-500 border-red-500/30 bg-red-500/10';
      default: return 'text-neutral-400 border-neutral-400/30 bg-neutral-400/10';
    }
  };
  
  const getRiskBg = (cat) => {
    switch (cat?.toUpperCase()) {
      case 'LOW':
      case 'SAFE':
      case 'NO THERMAL STRESS':
      case 'NO_THERMAL_STRESS':
      case 'COLD STRESS':
      case 'COLD_STRESS': return 'bg-green-500';
      case 'CAUTION': return 'bg-yellow-500';
      case 'MODERATE': return 'bg-amber-500';
      case 'STRONG':
      case 'HIGH':
      case 'EXTREME CAUTION':
      case 'EXTREME_CAUTION':
      case 'VERY_HIGH': return 'bg-orange-500';
      case 'EXTREME':
      case 'VERY_STRONG':
      case 'VERY STRONG':
      case 'DANGER':
      case 'EXTREME DANGER':
      case 'EXTREME_DANGER': return 'bg-red-500';
      default: return 'bg-neutral-500';
    }
  };

  const overallRisk = authoritativeRisk?.thermal_stress?.overall_thermal_stress || 'UNKNOWN';
  const dominantIndex = authoritativeRisk?.thermal_stress?.dominant_index?.toUpperCase() || 'NONE';
  const peakForecast = targetForecast?.prediction?.[dominantIndex.toLowerCase()]?.value?.toFixed(1) || '--';

  // Alert Panel Logic from authoritative risk
  let alertTitle = 'NO ACTIVE ALERTS';
  let alertPeriod = '--';
  let alertPeak = '--';
  let alertDriver = 'UTCI';
  let alertColorClass = 'text-green-500';
  let alertBgClass = 'bg-[#121827]/90 border-green-500/30';
  
  if (Array.isArray(riskData) && riskData.length > 0) {
    let worstRiskStr = 'LOW';
    let maxSeverity = -1;
    let worstHorizon = null;
    let worstPeak = 0;
    let wDriver = 'UTCI';
    
    // Map categories to severity for worst-case finding
    const getSev = (c) => {
      const s = c.toUpperCase();
      if (s.includes('EXTREME') || s.includes('DANGER') || s.includes('VERY_STRONG')) return 4;
      if (s.includes('STRONG') || s.includes('VERY_HIGH')) return 3;
      if (s.includes('MODERATE') || s.includes('CAUTION')) return 2;
      return 1;
    };

    riskData.forEach((r, idx) => {
      const cat = r?.thermal_stress?.overall_thermal_stress || 'LOW';
      const sev = getSev(cat);
      if (sev > maxSeverity) {
        maxSeverity = sev;
        worstRiskStr = cat;
        worstHorizon = (idx + 1) * 24;
        wDriver = r?.thermal_stress?.dominant_index?.toUpperCase() || 'NONE';
      }
    });
    
    // Match peak value with seqData
    if (worstHorizon && Array.isArray(seqData)) {
       const seqMatch = seqData.find(d => d.forecast_horizon_hours === worstHorizon);
       if (seqMatch && seqMatch.prediction && seqMatch.prediction[wDriver.toLowerCase()]) {
           worstPeak = seqMatch.prediction[wDriver.toLowerCase()].value;
       }
    }

    alertTitle = worstRiskStr + " STRESS";
    if (worstHorizon) {
       alertPeriod = `Next ${worstHorizon} hours`;
       if (worstHorizon > 24) {
          alertPeriod = `Between ${worstHorizon - 24} - ${worstHorizon} hours`;
       }
    }
    alertPeak = worstPeak > 0 ? worstPeak.toFixed(1) : '--';
    alertDriver = wDriver;
    
    const s = worstRiskStr.toUpperCase();
    if (s.includes('EXTREME') || s.includes('DANGER') || s.includes('VERY_STRONG')) {
       alertColorClass = 'text-red-500';
       alertBgClass = 'bg-[#1c0f13]/90 border-red-500/30';
    } else if (s.includes('STRONG') || s.includes('VERY_HIGH')) {
       alertColorClass = 'text-orange-500';
       alertBgClass = 'bg-[#1c120f]/90 border-orange-500/30';
    } else if (s.includes('MODERATE') || s.includes('CAUTION')) {
       alertColorClass = 'text-amber-500';
       alertBgClass = 'bg-[#1c160f]/90 border-amber-500/30';
    } else {
       alertColorClass = 'text-green-500';
       alertBgClass = 'bg-[#0f1c13]/90 border-green-500/30';
       alertTitle = 'NORMAL CONDITIONS';
    }
  }

  // Health Risk Logic based on the worst alert category
  let healthImpact = "Normal physiological responses. No immediate danger to general population.";
  let vulnerablePop = "None specifically at risk.";
  let recommendations = "Maintain normal hydration and outdoor activities.";
  
  if (alertTitle.includes("EXTREME")) {
     healthImpact = "High risk of heat stroke, cardiovascular failure, and severe dehydration. Thermoregulation severely compromised.";
     vulnerablePop = "Elderly (65+), outdoor laborers, pregnant women, infants.";
     recommendations = "Suspend outdoor labor. Open cooling centers. Issue Code Red emergency alerts.";
  } else if (alertTitle.includes("STRONG") || alertTitle.includes("VERY HIGH") || alertTitle.includes("VERY_HIGH")) {
     healthImpact = "Heat exhaustion extremely likely. Prolonged exposure causes severe cumulative thermal stress.";
     vulnerablePop = "Outdoor workers, unhoused populations, elderly.";
     recommendations = "Mandate strict rest/water breaks. Limit all outdoor activity between 11 AM - 4 PM.";
  } else if (alertTitle.includes("MODERATE") || alertTitle.includes("CAUTION")) {
     healthImpact = "Heat cramps and fatigue possible with physical exertion or prolonged exposure.";
     vulnerablePop = "Heavy laborers, athletes, individuals with comorbidities.";
     recommendations = "Increase fluid intake. Wear lightweight clothing. Monitor vulnerable groups.";
  }

  if (showLanding) {
    return <LandingPage onEnter={() => setShowLanding(false)} />;
  }

  return (
    <div className="flex h-screen bg-[#070b14] text-neutral-200 font-sans overflow-hidden">
      
      {/* 3D Background */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-40 mix-blend-screen">
        <iframe 
          src="https://my.spline.design/earthdayandnight-69HuPQYavcBmtugnKqtQeYIs/" 
          frameBorder="0" width="100%" height="100%" 
        />
      </div>

      {/* Sidebar */}
      <aside className="w-64 bg-[#0a0f1c]/90 backdrop-blur-xl border-r border-white/10 flex flex-col z-10">
        <div className="p-6">
          <div className="flex items-center gap-3 text-white mb-2">
            <Activity className="w-6 h-6 text-green-400" />
            <h1 className="text-xl font-bold tracking-wide">HeatPulse</h1>
          </div>
          <p className="text-[10px] text-neutral-400 uppercase tracking-widest">Extreme Heat. Early Warning.</p>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4">
          <button className="w-full flex items-center gap-3 px-4 py-3 bg-green-500/10 text-green-400 rounded-xl border border-green-500/20 font-medium">
            <div className="w-4 h-4 bg-green-400 rounded-sm" /> Dashboard
          </button>
          {['Forecast', 'History', 'Alerts', 'About'].map(item => (
            <button key={item} className="w-full flex items-center gap-3 px-4 py-3 text-neutral-400 hover:text-white hover:bg-white/5 rounded-xl transition-colors">
              <div className="w-4 h-4 border border-neutral-600 rounded-sm" /> {item}
            </button>
          ))}
        </nav>

        <div className="p-4 m-4 bg-white/5 border border-white/10 rounded-2xl">
          <h4 className="text-sm font-semibold text-green-400 mb-2">About HeatPulse</h4>
          <p className="text-xs text-neutral-400 leading-relaxed">
            AI-powered early warning system for extreme heat and human thermal stress.
          </p>
          <div className="mt-4 flex justify-end">
            <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
              <span className="text-green-400 text-xs">🌿</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col z-10 overflow-y-auto">
        {/* Header */}
        <header className="px-8 py-5 flex items-center justify-between border-b border-white/5 bg-black/20 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <MapPin className="w-5 h-5 text-green-400" />
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">Kochi, Kerala, India</h2>
              <p className="text-xs text-neutral-400 font-mono">9.9312° N, 76.2673° E</p>
            </div>
          </div>
          
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3 text-right">
              <Clock className="w-4 h-4 text-neutral-400" />
              <div>
                <p className="text-sm font-bold text-white font-mono">{now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</p>
                <p className="text-[10px] text-neutral-400">{now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</p>
              </div>
            </div>
            
            <div className="flex flex-col items-end gap-1.5">
              <button 
                onClick={fetchData}
                disabled={isLoading}
                className="flex items-center gap-2 px-4 py-1.5 bg-green-500/20 hover:bg-green-500/30 text-green-400 text-xs font-semibold rounded-full border border-green-500/30 transition-all disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <span className="text-[9px] text-neutral-500">Last updated: {lastUpdated}</span>
            </div>
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="p-8 grid grid-cols-12 gap-6">
          
          {/* Left Column (Span 8) */}
          <div className="col-span-8 space-y-6">
            
            {/* OVERALL HEAT RISK */}
            <div className="bg-[#121827]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6 flex items-center justify-between shadow-2xl">
              <div className="flex items-center gap-6">
                <div className="w-16 h-16 rounded-full bg-orange-500/20 border-2 border-orange-500/50 flex items-center justify-center">
                  <Thermometer className="w-8 h-8 text-orange-500" />
                </div>
                <div>
                  <p className="text-xs text-neutral-400 uppercase tracking-widest font-semibold mb-1">Overall Heat Risk</p>
                  <h2 className="text-4xl font-black text-orange-500 tracking-wide">{overallRisk.replace('_', ' ')}</h2>
                  <p className="text-sm text-neutral-300 mt-1">{targetForecast?.risk?.utci?.description || 'Loading...'}</p>
                </div>
              </div>
              
              <div className="flex gap-8 text-right">
                <div>
                  <p className="text-xs text-neutral-500 mb-1">Dominant Index</p>
                  <p className="text-xl font-bold text-orange-400">{dominantIndex}</p>
                </div>
                <div>
                  <p className="text-xs text-neutral-500 mb-1">Peak Forecast</p>
                  <p className="text-xl font-bold text-orange-400">{peakForecast} °C</p>
                </div>
                <div>
                  <p className="text-xs text-neutral-500 mb-1">Forecast Period</p>
                  <p className="text-base font-semibold text-white mt-1">Next {selectedHorizon} hours</p>
                </div>
              </div>
            </div>

            {/* THREE CARDS (REAL-TIME LIVE DATA) */}
            <div className="grid grid-cols-3 gap-6">
              {[
                { title: 'WBGT', key: 'wbgt', icon: Thermometer, color: 'text-green-400' },
                { title: 'UTCI', key: 'utci', icon: Activity, color: 'text-orange-500' },
                { title: 'HEAT INDEX', key: 'heat_index', icon: Flame, color: 'text-yellow-400' }
              ].map(idx => {
                const live = currentData?.[idx.key];
                const val = live?.value_c ? live.value_c.toFixed(2) : '--';
                
                // Parse a category string to map to colors
                let cat = 'LOW';
                let desc = live?.stress_category || 'Live calculation';
                const s = (desc).toUpperCase();
                if (s.includes('EXTREME')) cat = 'EXTREME';
                else if (s.includes('VERY STRONG')) cat = 'VERY_HIGH';
                else if (s.includes('STRONG')) cat = 'STRONG';
                else if (s.includes('MODERATE')) cat = 'MODERATE';
                else if (s.includes('CAUTION')) cat = 'CAUTION';
                
                const methodStr = live?.method ? (live.method.length > 25 ? live.method.substring(0, 22) + '...' : live.method) : 'Physics Engine';

                return (
                  <div key={idx.title} className="bg-[#121827]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-5 flex flex-col justify-between h-48">
                    <div className="flex justify-between items-start">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-full bg-white/5 border border-white/10 ${idx.color}`}>
                          <idx.icon className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-neutral-400 tracking-wide flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> LIVE {idx.title}
                          </p>
                          <p className="text-2xl font-bold text-white mt-1">{val} <span className="text-sm text-neutral-500">°C</span></p>
                        </div>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getRiskColor(cat)}`}>
                        {cat.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-xs text-neutral-400 mt-3 capitalize">{desc}</p>
                    <div className="mt-4 pt-4 border-t border-white/5 text-[10px] text-neutral-500 flex flex-col gap-1">
                      <p>Method: {methodStr}</p>
                      <p className="text-emerald-500/70">Real-time Weather Assimilation</p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* CHART & TIMELINE ROW */}
            <div className="grid grid-cols-3 gap-6">
              
              {/* CHART */}
              <div className="col-span-2 bg-[#121827]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wide">Kochi Forecast</h3>
                  <div className="flex gap-2 bg-black/40 p-1 rounded-lg border border-white/10">
                    {[24, 48, 72, 96, 120].map(h => (
                      <button 
                        key={h}
                        onClick={() => setSelectedHorizon(h)}
                        className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${selectedHorizon === h ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'text-neutral-500 hover:text-white'}`}
                      >
                        {h}h
                      </button>
                    ))}
                  </div>
                </div>
                
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                      <XAxis dataKey="name" stroke="#ffffff40" fontSize={10} tickLine={false} axisLine={false} />
                      <YAxis stroke="#ffffff40" fontSize={10} tickLine={false} axisLine={false} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0a0f1c', border: '1px solid #ffffff20', borderRadius: '8px', fontSize: '12px' }}
                        itemStyle={{ fontWeight: 'bold' }}
                      />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      <Line type="monotone" dataKey="WBGT" stroke="#4ade80" strokeWidth={2} dot={{ r: 3, fill: '#4ade80' }} />
                      <Line type="monotone" dataKey="UTCI" stroke="#f97316" strokeWidth={2} dot={{ r: 3, fill: '#f97316' }} />
                      <Line type="monotone" dataKey="HeatIndex" name="Heat Index" stroke="#facc15" strokeWidth={2} dot={{ r: 3, fill: '#facc15' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <p className="text-[10px] text-neutral-500 mt-4">All times in local time (IST)</p>
              </div>

              {/* TIMELINE */}
              <div className="bg-[#121827]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6 relative">
                <h3 className="text-sm font-bold text-white uppercase tracking-wide mb-6">Risk Timeline <span className="text-neutral-500 normal-case font-normal">(Next {selectedHorizon} Hours)</span></h3>
                <div className="relative pl-2 h-[200px] flex flex-col justify-between">
                  <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-white/10" />
                  
                  {chartData.map((d, i) => {
                    // Match to forecast object to get risk
                    const h = d.horizon;
                    let cat = 'UNKNOWN';
                    if (h === 0) {
                      const stressStr = currentData?.utci?.stress_category?.toUpperCase() || '';
                      if (stressStr.includes('EXTREME')) cat = 'EXTREME';
                      else if (stressStr.includes('VERY STRONG')) cat = 'VERY_HIGH';
                      else if (stressStr.includes('STRONG')) cat = 'STRONG';
                      else if (stressStr.includes('MODERATE')) cat = 'MODERATE';
                      else cat = 'LOW';
                    } else {
                      const f = Array.isArray(seqData) ? seqData.find(x => x.forecast_horizon_hours === h) : null;
                      cat = f?.risk?.utci?.category || 'LOW';
                    }
                    
                    return (
                      <div key={d.name} className="flex items-center gap-4 relative z-10">
                        <div className={`w-3 h-3 rounded-full border-2 border-[#121827] shadow-sm ${getRiskBg(cat)}`} />
                        <div className="w-20 text-right leading-tight whitespace-nowrap">
                          <p className="text-xs font-bold text-white">{d.name}</p>
                          <p className="text-[9px] text-neutral-400">{d.fullTime}</p>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${getRiskColor(cat)}`}>
                          {cat.replace('_', ' ')}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

            </div>

            {/* BOTTOM DIAGRAM */}
            <div className="bg-[#121827]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6">
              <h3 className="text-sm font-bold text-white uppercase tracking-wide mb-6">How HeatPulse Works</h3>
              <div className="flex justify-between items-start gap-4">
                {[
                  { icon: CloudRain, title: "1. Live Weather", desc: "Real-time data from Open-Meteo" },
                  { icon: Clock, title: "2. Historical Context", desc: "Recent history builds the full picture" },
                  { icon: Activity, title: "3. Thermal Physics", desc: "Calculate WBGT, UTCI & Heat Index" },
                  { icon: Layers, title: "4. 90 Features", desc: "Lags, rolling stats, trends & more" },
                  { icon: Flame, title: "5. ML Forecast", desc: "Ridge & RF models forecast up to 120h" },
                  { icon: ShieldAlert, title: "6. Risk Classification", desc: "Convert forecasts into human risk levels" }
                ].map((s, i) => (
                  <div key={s.title} className="flex flex-col items-center text-center max-w-[100px] relative">
                    <div className="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-3">
                      <s.icon className="w-5 h-5 text-neutral-300" />
                    </div>
                    <p className="text-[10px] font-bold text-white mb-1">{s.title}</p>
                    <p className="text-[9px] text-neutral-500 leading-tight">{s.desc}</p>
                    {i < 5 && <div className="hidden lg:block absolute top-5 -right-8 w-6 h-[1px] bg-white/20" />}
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Right Column (Span 4) */}
          <div className="col-span-4 space-y-6">
            
            {/* ALERT PANEL */}
            <div className={`backdrop-blur-xl border rounded-3xl p-6 relative overflow-hidden transition-colors duration-500 ${alertBgClass}`}>
              <div className={`absolute top-0 right-0 p-4 opacity-10 ${alertColorClass}`}>
                <AlertTriangle className="w-24 h-24" />
              </div>
              <div className={`flex items-center gap-2 mb-4 ${alertColorClass}`}>
                <AlertTriangle className="w-5 h-5" />
                <h3 className="text-sm font-bold tracking-widest uppercase">Heatwave Alert</h3>
              </div>
              <h2 className={`text-2xl font-black mb-6 ${alertColorClass.replace('text-', 'text-opacity-80 text-')}`}>{alertTitle.replace('_', ' ')}</h2>
              
              <div className="space-y-4 text-sm">
                <div>
                  <p className="text-neutral-400 text-xs mb-1">Expected during</p>
                  <p className="font-semibold text-white">{alertPeriod}</p>
                </div>
                <div>
                  <p className="text-neutral-400 text-xs mb-1">Driven by</p>
                  <p className="font-semibold text-white">{alertDriver}</p>
                </div>
                <div>
                  <p className="text-neutral-400 text-xs mb-1">Peak Forecast</p>
                  <p className="font-semibold text-white">{alertPeak} °C</p>
                </div>
              </div>
            </div>

            {/* HUMAN HEALTH IMPACT */}
            <div className="bg-[#121827]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6">
              <div className="flex items-center gap-2 mb-4 text-purple-400">
                <Activity className="w-5 h-5" />
                <h3 className="text-sm font-bold tracking-widest uppercase">Estimated Health Risk</h3>
              </div>
              
              <div className="space-y-4">
                <div>
                  <p className="text-neutral-400 text-[10px] uppercase font-bold tracking-wider mb-1">Physiological Impact</p>
                  <p className="text-sm text-white leading-relaxed">{healthImpact}</p>
                </div>
                <div>
                  <p className="text-neutral-400 text-[10px] uppercase font-bold tracking-wider mb-1">Vulnerable Demographics</p>
                  <p className="text-sm text-white leading-relaxed">{vulnerablePop}</p>
                </div>
                <div>
                  <p className="text-neutral-400 text-[10px] uppercase font-bold tracking-wider mb-1">Recommended Action</p>
                  <p className="text-sm text-emerald-400 leading-relaxed font-semibold">{recommendations}</p>
                </div>
              </div>
            </div>

            {/* CURRENT WEATHER */}
            <div className="bg-[#121827]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6">
              <h3 className="text-sm font-bold text-white uppercase tracking-wide mb-5">Current Weather <span className="text-neutral-500 normal-case font-normal">(Input to Model)</span></h3>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-2 text-neutral-400"><Thermometer className="w-4 h-4" /> Temperature (2m)</div>
                  <div className="font-mono text-white">{currentData?.inputs?.temperature_c ?? '--'} °C</div>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-2 text-neutral-400"><Droplets className="w-4 h-4" /> Relative Humidity</div>
                  <div className="font-mono text-white">{currentData?.inputs?.relative_humidity_pct ?? '--'} %</div>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-2 text-neutral-400"><Wind className="w-4 h-4" /> Wind Speed (10m)</div>
                  <div className="font-mono text-white">{currentData?.inputs?.wind_speed_ms ?? '--'} m/s</div>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-2 text-neutral-400"><Activity className="w-4 h-4" /> Pressure</div>
                  <div className="font-mono text-white">{currentData?.inputs?.pressure_hpa ?? '--'} hPa</div>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-2 text-neutral-400"><Sun className="w-4 h-4" /> Shortwave Radiation</div>
                  <div className="font-mono text-white">{currentData?.inputs?.shortwave_radiation_wm2 ?? '--'} W/m²</div>
                </div>
              </div>
              <p className="text-[10px] text-neutral-500 mt-5 pt-3 border-t border-white/5">Source: Open-Meteo</p>
            </div>
            {/* THERMAL PHYSICS ENGINE */}
            <div className="bg-[#121827]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6">
              <div className="flex items-center gap-2 mb-4 text-emerald-400">
                <Activity className="w-5 h-5" />
                <h3 className="text-sm font-bold tracking-widest uppercase">Thermal Engine</h3>
              </div>
              
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between items-end mb-1">
                    <p className="text-neutral-400 text-[10px] uppercase font-bold tracking-wider">UTCI (Universal Thermal Climate)</p>
                    <p className="text-xs font-bold text-white">{currentData?.utci?.value_c ? `${currentData.utci.value_c.toFixed(2)} °C` : '--'}</p>
                  </div>
                  <p className="text-xs text-white leading-relaxed font-mono bg-black/30 p-2 rounded border border-white/5">{currentData?.utci?.method || 'UTCI Polynomial (Fiala model)'}</p>
                </div>
                <div>
                  <div className="flex justify-between items-end mb-1">
                    <p className="text-neutral-400 text-[10px] uppercase font-bold tracking-wider">WBGT (Wet-Bulb Globe Temp)</p>
                    <p className="text-xs font-bold text-white">{currentData?.wbgt?.value_c ? `${currentData.wbgt.value_c.toFixed(2)} °C` : '--'}</p>
                  </div>
                  <p className="text-xs text-white leading-relaxed font-mono bg-black/30 p-2 rounded border border-white/5">{currentData?.wbgt?.method || 'Liljegren Heat Balance Solver'}</p>
                </div>
                <div>
                  <div className="flex justify-between items-end mb-1">
                    <p className="text-neutral-400 text-[10px] uppercase font-bold tracking-wider">Mean Radiant Temperature</p>
                    <p className="text-xs font-bold text-white">{currentData?.mrt?.value_c ? `${currentData.mrt.value_c.toFixed(2)} °C` : '--'}</p>
                  </div>
                  <p className="text-xs text-white leading-relaxed font-mono bg-black/30 p-2 rounded border border-white/5">{currentData?.mrt?.method || 'ASHRAE Solar Geometry Model'}</p>
                </div>
              </div>
            </div>

            {/* MODEL INFO */}
            <div className="bg-[#121827]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6">
              <h3 className="text-sm font-bold text-green-400 uppercase tracking-wide mb-4">Model Information</h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between"><span className="text-neutral-500">Models</span><span className="text-white">Ridge, Random Forest</span></div>
                <div className="flex justify-between"><span className="text-neutral-500">Indices</span><span className="text-white">WBGT, UTCI, Heat Index</span></div>
                <div className="flex justify-between"><span className="text-neutral-500">Forecast Horizons</span><span className="text-white">24h, 48h, 72h, 96h, 120h</span></div>
                <div className="flex justify-between"><span className="text-neutral-500">Validation Location</span><span className="text-white">Kochi, Kerala, India</span></div>
                <div className="flex justify-between"><span className="text-neutral-500">Test Period</span><span className="text-white">08 Feb 2025 - 27 Jun 2026</span></div>
                <div className="flex justify-between"><span className="text-neutral-500">Test Samples</span><span className="text-white">1,172 observations</span></div>
              </div>
              <div className="mt-4 p-3 rounded-xl bg-green-500/10 border border-green-500/20 text-[10px] text-green-300">
                "Model performance has been evaluated on unseen Kochi/ERA5 data and may not generalize to other locations."
              </div>
            </div>

            {/* KOCHI MAP & WARD TABLE */}
            <div className="col-span-12 bg-[#121827]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wide">Ward-Level Vulnerability & Impact</h3>
                <span className="text-[10px] text-green-400 font-bold tracking-wider uppercase flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" /> {wardsData?.length || 0} Wards Loaded
                </span>
              </div>
              <div className="w-full h-48 rounded-xl bg-black/50 border border-white/5 relative overflow-hidden mb-4">
                <MapContainer center={[9.96, 76.31]} zoom={11} style={{ height: '100%', width: '100%', backgroundColor: '#02050b' }} zoomControl={false}>
                  <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?api_key=cb1_2p2f_1_9616035ff449cee0877c0c56"
                    attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                  />
                  {wardsData?.map(w => {
                     const color = getRiskColor(w.risk?.today?.overall || 'LOW');
                     const hex = color.includes('red') ? '#ef4444' : color.includes('orange') ? '#f97316' : color.includes('amber') || color.includes('yellow') ? '#facc15' : '#4ade80';
                     return <CircleMarker key={w.ward_no} center={[w.latitude, w.longitude]} radius={6} pathOptions={{ color: hex, fillColor: hex, fillOpacity: 0.6, stroke: false }} />;
                  })}
                </MapContainer>
              </div>
              
              <div className="overflow-x-auto overflow-y-auto max-h-64 rounded-lg border border-white/5">
                <table className="w-full text-left text-[10px] text-neutral-300">
                  <thead className="text-[9px] uppercase bg-black/40 text-neutral-400 sticky top-0 z-10">
                    <tr>
                      <th className="px-2 py-2">Ward No</th>
                      <th className="px-2 py-2">Ward Name</th>
                      <th className="px-2 py-2">Temperature</th>
                      <th className="px-2 py-2">Feels Like</th>
                      <th className="px-2 py-2">Humidity</th>
                      <th className="px-2 py-2">Wind</th>
                      <th className="px-2 py-2">Rain</th>
                      <th className="px-2 py-2">Weather</th>
                      <th className="px-2 py-2">WBGT</th>
                      <th className="px-2 py-2">UTCI</th>
                      <th className="px-2 py-2">Heat Index</th>
                      <th className="px-2 py-2">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {wardsData?.map(w => (
                      <tr key={w.ward_no} className="border-b border-white/5 hover:bg-white/5">
                        <td className="px-2 py-2 font-bold text-white whitespace-nowrap">{w.ward_no}</td>
                        <td className="px-2 py-2 font-bold text-white whitespace-nowrap">{w.ward_name}</td>
                        <td className="px-2 py-2 whitespace-nowrap">{w.weather?.today?.temperature_max_c} °C</td>
                        <td className="px-2 py-2 whitespace-nowrap">{w.weather?.today?.apparent_temperature_mean_c} °C</td>
                        <td className="px-2 py-2 whitespace-nowrap">{w.weather?.today?.humidity_mean_percent}%</td>
                        <td className="px-2 py-2 whitespace-nowrap">{w.weather?.today?.wind_speed_mean_kmh} km/h</td>
                        <td className="px-2 py-2 whitespace-nowrap">{w.weather?.today?.precipitation_sum_mm} mm</td>
                        <td className="px-2 py-2 whitespace-nowrap">{w.weather?.today?.weather_condition}</td>
                        <td className="px-2 py-2 whitespace-nowrap">{w.heat_stress?.today?.wbgt?.prediction_c?.toFixed(1) ?? '--'}</td>
                        <td className="px-2 py-2 whitespace-nowrap">{w.heat_stress?.today?.utci?.prediction_c?.toFixed(1) ?? '--'}</td>
                        <td className="px-2 py-2 whitespace-nowrap">{w.heat_stress?.today?.heat_index?.prediction_c !== null ? w.heat_stress?.today?.heat_index?.prediction_c?.toFixed(1) : 'N/A'}</td>
                        <td className="px-2 py-2 whitespace-nowrap"><span className={`px-1.5 py-0.5 rounded font-bold border ${getRiskColor(w.risk?.today?.overall)}`}>{w.risk?.today?.overall?.replace('_',' ') || 'UNKNOWN'}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>


          </div>
        </div>
      </main>
    </div>
  );
}
