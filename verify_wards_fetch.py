import urllib.request
import json
import time

def verify():
    url = "http://localhost:8000/api/v1/wards/weather"
    print(f"Fetching from {url} ...")
    req = urllib.request.urlopen(url)
    data = json.loads(req.read())
    
    wards = data.get('wards', [])
    print(f"Wards returned: {len(wards)}")
    
    target_wards = ["Fort Kochi", "Mattanchery", "Edakochi", "Vyttila", "Edappally", "Kunnumpuram", "Ernakulam Central", "Thattazham"]
    found = []
    
    for w in wards:
        if w['ward_name'] in target_wards or len(found) < 5:
            found.append(w)
            
    for w in found[:10]:
        print(f"\nWARD: {w['ward_no']} - {w['ward_name']}")
        print(f"Coords: {w['latitude']}, {w['longitude']}")
        
        if not w.get('weather'):
            print(f"Status: {w['status']} (Error: {w.get('error')})")
            continue
            
        today = w['weather']['today']
        print(f"Weather (Today/Tomorrow/Day+2): {today['temperature_max_c']}C, {w['weather']['tomorrow']['temperature_max_c']}C, {w['weather']['day_plus_2']['temperature_max_c']}C")
        print(f"Details (Today): Hum: {today['humidity_mean_percent']}%, Wind: {today['wind_speed_mean_kmh']}km/h, Rain: {today['precipitation_sum_mm']}mm, Cond: {today['weather_condition']}")
        print(f"Provenance: {w['provenance']}")
        
        hs = w['heat_stress']['today']
        print(f"WBGT: {hs['wbgt']['prediction_c']} (model: {hs['wbgt'].get('model', 'ML Model')})")
        print(f"UTCI: {hs['utci']['prediction_c']} (model: {hs['utci'].get('model', 'ML Model')})")
        print(f"Heat Index: {hs['heat_index'].get('prediction_c')} (risk: {hs['heat_index'].get('risk', 'UNKNOWN')})")
        
        risk = w['risk']['today']
        print(f"Risk: {risk['overall']}")

if __name__ == '__main__':
    verify()
