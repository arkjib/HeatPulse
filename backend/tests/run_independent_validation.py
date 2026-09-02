import lwbgt
from datetime import datetime, timezone
import math
import sys
import os

# Add parent dir to path so we can import our app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.thermal.wbgt import calculate_wbgt
from app.thermal.radiant_temperature import calculate_mrt

def run_validation():
    print("==========================================================")
    print("INDEPENDENT NUMERICAL VALIDATION: LILJEGREN OUTDOOR WBGT")
    print("Reference Implementation: lwbgt (C-library direct port)")
    print("==========================================================")
    
    cases = [
        {
            "name": "Hot + Humid + Strong Solar",
            "dt": datetime(2023, 7, 15, 6, 0, tzinfo=timezone.utc), # 11:30 AM India
            "lat": 28.61, "lon": 77.23,
            "ta": 38.0, "rh": 65.0, "wind": 1.5, "ghi": 850.0, "dni": 700.0, "diffuse": 150.0, "p": 1005.0
        },
        {
            "name": "Hot + Dry + Moderate Solar",
            "dt": datetime(2023, 7, 15, 20, 0, tzinfo=timezone.utc), # 1:00 PM LA
            "lat": 34.05, "lon": -118.24,
            "ta": 42.0, "rh": 15.0, "wind": 3.0, "ghi": 600.0, "dni": 500.0, "diffuse": 100.0, "p": 1010.0
        },
        {
            "name": "Nighttime (Zero Solar)",
            "dt": datetime(2023, 7, 15, 20, 0, tzinfo=timezone.utc), # 1:30 AM India
            "lat": 28.61, "lon": 77.23,
            "ta": 29.0, "rh": 80.0, "wind": 1.0, "ghi": 0.0, "dni": 0.0, "diffuse": 0.0, "p": 1000.0
        },
        {
            "name": "Weak Solar + High Wind",
            "dt": datetime(2023, 11, 15, 12, 0, tzinfo=timezone.utc), # 12:00 PM London
            "lat": 51.50, "lon": -0.12,
            "ta": 15.0, "rh": 70.0, "wind": 8.0, "ghi": 200.0, "dni": 150.0, "diffuse": 50.0, "p": 1015.0
        }
    ]

    for c in cases:
        print(f"\n--- CASE: {c['name']} ---")
        
        # 1. INDEPENDENT REFERENCE (LWBGT)
        ref_input = lwbgt.Input(
            year=c['dt'].year,
            month=c['dt'].month,
            day=c['dt'].day,
            hour=c['dt'].hour,
            minute=c['dt'].minute,
            gmt_offset_hours=0,
            averaging_minutes=0,
            urban=0,
            latitude_deg_north=c['lat'],
            longitude_deg_east=c['lon'],
            solar_w_m2=c['ghi'],
            pressure_hpa=c['p'],
            air_temperature_c=c['ta'],
            relative_humidity_percent=c['rh'],
            wind_speed_m_s=c['wind'],
            wind_height_m=10.0,
            vertical_temperature_difference_c=0.0
        )
        ref_res = lwbgt.calculate(ref_input)
        
        # 2. OUR IMPLEMENTATION
        our_mrt = calculate_mrt(
            temperature_c=c['ta'], 
            shortwave_rad=c['ghi'], 
            direct_rad=c['dni'], 
            diffuse_rad=c['diffuse'], 
            dni=c['dni'],
            latitude=c['lat'],
            longitude=c['lon'],
            timestamp=c['dt']
        )
        
        mrt_val = our_mrt["value_c"]
        our_wbgt = calculate_wbgt(c['ta'], c['rh'], c['wind'], mrt_val, c['ghi'])
        
        print(f"Independent Reference:")
        print(f"  Tnwb: {ref_res.natural_wet_bulb_c:.2f} C")
        print(f"  Tg:   {ref_res.globe_temperature_c:.2f} C")
        print(f"  WBGT: {ref_res.wbgt_c:.2f} C")
        
        print(f"Our Derived Pipeline:")
        print(f"  Tnwb: {our_wbgt['tnwb_c']:.2f} C")
        print(f"  Tg:   {our_wbgt['tg_c']:.2f} C (driven by MRT: {mrt_val:.2f})")
        print(f"  WBGT: {our_wbgt['value_c']:.2f} C")
        
        diff_tnwb = abs(ref_res.natural_wet_bulb_c - our_wbgt['tnwb_c'])
        diff_tg = abs(ref_res.globe_temperature_c - our_wbgt['tg_c'])
        diff_wbgt = abs(ref_res.wbgt_c - our_wbgt['value_c'])
        
        print(f"Absolute Differences:")
        print(f"  Tnwb: {diff_tnwb:.2f} C")
        print(f"  Tg:   {diff_tg:.2f} C")
        print(f"  WBGT: {diff_wbgt:.2f} C")

if __name__ == "__main__":
    run_validation()
