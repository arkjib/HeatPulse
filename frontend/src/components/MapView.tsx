import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icons in React Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapViewProps {
  lat: number;
  lon: number;
}

// Component to handle dynamic map centering
function MapUpdater({ lat, lon }: { lat: number, lon: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([lat, lon], 10, { animate: true });
  }, [lat, lon, map]);
  return null;
}

export const MapView: React.FC<MapViewProps> = ({ lat, lon }) => {
  return (
    <MapContainer 
      center={[lat, lon]} 
      zoom={10} 
      style={{ height: '100%', width: '100%', position: 'absolute', top: 0, left: 0 }}
      zoomControl={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
      />
      <MapUpdater lat={lat} lon={lon} />
      <Marker position={[lat, lon]} />
    </MapContainer>
  );
};
