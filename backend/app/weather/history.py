import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cache"

class WeatherCache:
    """
    Simple file-based persistent cache for weather API responses.
    Prevents redundant calls to the external provider for the same location.
    """
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, lat: float, lon: float) -> Path:
        # Round coordinates slightly to group nearby requests and improve cache hit rate
        return CACHE_DIR / f"weather_{round(lat, 3)}_{round(lon, 3)}.json"

    def get(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        path = self._get_cache_path(lat, lon)
        if not path.exists():
            return None
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
                
            if time.time() - data["cached_at"] > self.ttl_seconds:
                return None  # Expired
                
            return data["payload"]
        except Exception as e:
            logger.warning(f"Failed to read cache for {lat},{lon}: {e}")
            return None

    def set(self, lat: float, lon: float, payload: Dict[str, Any]) -> None:
        path = self._get_cache_path(lat, lon)
        try:
            with open(path, "w") as f:
                json.dump({
                    "cached_at": time.time(),
                    "payload": payload
                }, f)
        except Exception as e:
            logger.warning(f"Failed to write cache for {lat},{lon}: {e}")

weather_cache = WeatherCache(ttl_seconds=3600)  # 1 hour cache
