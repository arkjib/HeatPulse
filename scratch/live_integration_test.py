import sys
import asyncio
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.forecast import forecast_service

async def main():
    print("Initiating REAL Integration Test with Live Open-Meteo Data...")
    lat, lon = 9.9312, 76.2673 # Kochi
    horizon = 72
    
    print(f"Location: ({lat}, {lon})")
    print(f"Horizon: {horizon}h")
    
    try:
        response = await forecast_service.get_forecast_sequence(lat, lon)
        print("\nIntegration Test Successful! Output:\n")
        print(response[0].model_dump_json(indent=2))
    except Exception as e:
        print(f"\nIntegration Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
