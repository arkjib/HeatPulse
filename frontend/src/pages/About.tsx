export function About() {
  return (
    <div className="max-w-2xl mx-auto py-12 px-6">
      <h1 className="text-3xl font-black text-slate-800 mb-6">About HeatPulse</h1>
      <p className="text-lg text-slate-700 leading-relaxed mb-6">
        HeatPulse is an extreme heat early-warning system designed to estimate human thermal stress using:
      </p>
      <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 flex flex-col items-center gap-4 text-slate-800 font-bold mb-8 shadow-sm">
        <div className="text-xl bg-white px-6 py-2 rounded-lg shadow-sm border border-slate-100">Live Weather</div>
        <div className="text-slate-400">+</div>
        <div className="text-xl bg-white px-6 py-2 rounded-lg shadow-sm border border-slate-100">Thermal Physics</div>
        <div className="text-slate-400">+</div>
        <div className="text-xl bg-white px-6 py-2 rounded-lg shadow-sm border border-slate-100">Machine Learning</div>
      </div>
      
      <div className="space-y-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200">
          <h2 className="text-lg font-bold text-slate-800 mb-2">WBGT (Wet-Bulb Globe Temperature)</h2>
          <p className="text-slate-600 text-sm leading-relaxed">The global standard for occupational heat stress. It measures the combined effect of temperature, humidity, wind, and solar radiation on the human body.</p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200">
          <h2 className="text-lg font-bold text-slate-800 mb-2">UTCI (Universal Thermal Climate Index)</h2>
          <p className="text-slate-600 text-sm leading-relaxed">A modern biometeorological index that models how the human body physiologically responds to the outdoor thermal environment.</p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200">
          <h2 className="text-lg font-bold text-slate-800 mb-2">Heat Index</h2>
          <p className="text-slate-600 text-sm leading-relaxed">Also known as the apparent temperature, this is what the temperature feels like to the human body when relative humidity is combined with the air temperature.</p>
        </div>
      </div>
    </div>
  );
}
