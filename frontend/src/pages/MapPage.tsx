import { MapView } from '../components/MapView';

interface MapPageProps {
  lat: number;
  lon: number;
}

export function MapPage({ lat, lon }: MapPageProps) {
  return (
    <div className="h-[calc(100vh-160px)] p-6 flex flex-col">
      <h2 className="text-xl font-bold text-slate-800 mb-4">Location Map</h2>
      <div className="flex-1 rounded-xl overflow-hidden shadow-sm border border-slate-200">
        <MapView lat={lat} lon={lon} />
      </div>
    </div>
  );
}
