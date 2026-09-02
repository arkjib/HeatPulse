from typing import Any, Dict, List
from datetime import datetime
from app.schemas.weather import CurrentWeather, HourlyWeather, WeatherForecast, WeatherBase

class WeatherNormalizer:
    @staticmethod
    def _safe_get_radiation(data_dict: Dict[str, Any], key: str, index: int = None) -> float | None:
        if index is not None:
            # Array case (hourly)
            val_array = data_dict.get(key)
            if val_array is None or index >= len(val_array):
                return None
            val = val_array[index]
        else:
            # Scalar case (current)
            val = data_dict.get(key)
            
        if val is not None and val < 0:
            val = 0.0
        return val

    @staticmethod
    def normalize_current(data: Dict[str, Any]) -> CurrentWeather:
        try:
            current = data["current"]
            lat = data["latitude"]
            lon = data["longitude"]
            
            base = WeatherBase(
                timestamp=datetime.fromisoformat(current["time"]),
                temperature=current["temperature_2m"],
                relative_humidity=current["relative_humidity_2m"],
                wind_speed=current["wind_speed_10m"],
                shortwave_radiation=WeatherNormalizer._safe_get_radiation(current, "shortwave_radiation"),
                direct_radiation=WeatherNormalizer._safe_get_radiation(current, "direct_radiation"),
                diffuse_radiation=WeatherNormalizer._safe_get_radiation(current, "diffuse_radiation"),
                direct_normal_irradiance=WeatherNormalizer._safe_get_radiation(current, "direct_normal_irradiance"),
                pressure=current["surface_pressure"]
            )
            
            return CurrentWeather(
                latitude=lat,
                longitude=lon,
                weather=base
            )
        except KeyError as e:
            raise ValueError(f"Missing expected key in provider response: {e}")

    @staticmethod
    def normalize_forecast(data: Dict[str, Any]) -> WeatherForecast:
        try:
            hourly = data["hourly"]
            lat = data["latitude"]
            lon = data["longitude"]
            
            times = hourly["time"]
            temps = hourly["temperature_2m"]
            rhs = hourly["relative_humidity_2m"]
            winds = hourly["wind_speed_10m"]
            pressures = hourly["surface_pressure"]
            
            forecasts: List[HourlyWeather] = []
            
            for i in range(len(times)):
                base = WeatherBase(
                    timestamp=datetime.fromisoformat(times[i]),
                    temperature=temps[i],
                    relative_humidity=rhs[i],
                    wind_speed=winds[i],
                    shortwave_radiation=WeatherNormalizer._safe_get_radiation(hourly, "shortwave_radiation", i),
                    direct_radiation=WeatherNormalizer._safe_get_radiation(hourly, "direct_radiation", i),
                    diffuse_radiation=WeatherNormalizer._safe_get_radiation(hourly, "diffuse_radiation", i),
                    direct_normal_irradiance=WeatherNormalizer._safe_get_radiation(hourly, "direct_normal_irradiance", i),
                    pressure=pressures[i]
                )
                forecasts.append(HourlyWeather(**base.model_dump()))
                
            return WeatherForecast(
                latitude=lat,
                longitude=lon,
                forecast=forecasts
            )
        except (KeyError, IndexError) as e:
            raise ValueError(f"Malformed provider forecast response: {e}")
