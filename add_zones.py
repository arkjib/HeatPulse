with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "import { MapContainer, TileLayer, CircleMarker } from 'react-leaflet';",
    "import { MapContainer, TileLayer, CircleMarker, GeoJSON } from 'react-leaflet';"
)

content = content.replace("  const [wardsData, setWardsData] = useState([]);", "  const [wardsData, setWardsData] = useState([]);\n  const [geoJsonData, setGeoJsonData] = useState(null);")

fetch_injection = '''      // Fetch wards in background
      fetch(/api/v1/wards/weather)
        .then(res => res.json())
        .then(wrd => setWardsData(wrd?.wards || []))
        .catch(e => console.error(e));
        
      // Fetch GeoJSON
      fetch(/KCH_wards.json)
        .then(res => res.json())
        .then(data => setGeoJsonData(data))
        .catch(e => console.error("Failed to load geojson", e));'''
content = content.replace('''      // Fetch wards in background
      fetch(/api/v1/wards/weather)
        .then(res => res.json())
        .then(wrd => setWardsData(wrd?.wards || []))
        .catch(e => console.error(e));''', fetch_injection)

style_logic = '''
                    const getFeatureStyle = (feature) => {
                      const wardNo = feature.properties.WARD_NO;
                      const ward = wardsData?.find(w => w.ward_no === wardNo);
                      let hex = '#4ade80'; 
                      if (ward) {
                         const color = getRiskColor(ward.risk?.today?.overall || 'LOW');
                         hex = color.includes('red') ? '#ef4444' : color.includes('orange') ? '#f97316' : color.includes('amber') || color.includes('yellow') ? '#facc15' : '#4ade80';
                      }
                      return {
                        fillColor: hex,
                        weight: 1,
                        opacity: 0.8,
                        color: '#000',
                        fillOpacity: 0.5
                      };
                    };
                    
                    const onEachFeature = (feature, layer) => {
                      if (feature.properties && feature.properties.WARD_NAME) {
                        const ward = wardsData?.find(w => w.ward_no === feature.properties.WARD_NO);
                        const risk = ward?.risk?.today?.overall || 'UNKNOWN';
                        layer.bindPopup(<strong>Ward : </strong><br/>Risk: );
                      }
                    };
'''

content = content.replace('''                    <TileLayer
                      url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?api_key=cb1_2p2f_1_9616035ff449cee0877c0c56"
                      attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                    />''', '''                    <TileLayer
                      url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?api_key=cb1_2p2f_1_9616035ff449cee0877c0c56"
                      attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                    />''' + style_logic + '''
                    {geoJsonData && wardsData.length > 0 && (
                      <GeoJSON 
                        key={wardsData.length} 
                        data={geoJsonData} 
                        style={getFeatureStyle}
                        onEachFeature={onEachFeature}
                      />
                    )}''')

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Success")
