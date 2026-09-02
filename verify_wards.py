import json

def verify():
    with open('wards_response.json', 'r') as f:
        data = json.load(f)
        wards = data.get('wards', [])
        
        print(f"Wards returned: {len(wards)}")
        
        target_wards = ["Fort Kochi", "Mattanchery", "Edakochi", "Vyttila", "Edappally", "Kunnumpuarm", "Ernakulam Central", "Thattazham"]
        found = []
        
        for w in wards:
            if w['ward_name'] in target_wards or len(found) < 5:
                found.append(w)
                
        for w in found[:10]:
            print(f"\nWARD: {w['ward_no']} - {w['ward_name']}")
            print(f"Coords: {w['latitude']}, {w['longitude']}")
            
            today = w['weather']['today']
            print(f"Weather (Today/Tomorrow/Day+2): {today['temperature_max_c']}C, {w['weather']['tomorrow']['temperature_max_c']}C, {w['weather']['day_after_tomorrow']['temperature_max_c']}C")
            print(f"Details (Today): Hum: {today['humidity_mean_percent']}%, Wind: {today['wind_speed_mean_kmh']}km/h, Rain: {today['precipitation_sum_mm']}mm, Cond: {today['weather_condition']}")
            print(f"Provenance: {w['provenance']}")
            
            hs = w['heat_stress']['today']
            print(f"WBGT: {hs['wbgt']['prediction_c']} (method: {hs['wbgt']['method']})")
            print(f"UTCI: {hs['utci']['prediction_c']} (method: {hs['utci']['method']})")
            print(f"Heat Index: {hs['heat_index'].get('prediction_c')} (status: {hs['heat_index']['status']})")
            
            risk = w['risk']['today']
            print(f"Risk: {risk['overall']} (Driver: {risk.get('dominant_index', 'Unknown')})")
            
if __name__ == '__main__':
    verify()
