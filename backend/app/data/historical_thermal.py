"""
historical_thermal.py
----------------------
Iterates over an hourly historical weather sequence from the Open-Meteo
archive API response and applies the validated STEP 3 thermal engine to
each hour, producing an enriched list of dicts ready for dataset building.

IMPORTANT: This module is the ONLY place historical thermal indices are
computed. It calls the validated app.thermal.* engine — it does NOT
duplicate equations.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def _safe(val: Optional[float], min_val: float = 0.0) -> Optional[float]:
    """Clamp negatives to zero, pass None through (None = missing, not nighttime 0)."""
    if val is None:
        return None
    return max(val, min_val)


def compute_thermal_history(
    raw: Dict[str, Any],
    lat: float,
    lon: float,
) -> List[Dict[str, Any]]:
    """
    Convert an Open-Meteo archive API response dict into a list of hourly
    records, each enriched with thermal indices from the STEP 3 engine.

    Parameters
    ----------
    raw  : parsed JSON from HistoricalWeatherClient.fetch()
    lat  : latitude (passed through to lwbgt / MRT calculations)
    lon  : longitude

    Returns
    -------
    List of dicts — one per hour — with meteorological + thermal fields.
    Missing thermal values are None (not fabricated).
    """
    # Import here so the module can be used without the full app context
    # (e.g., directly in training scripts).
    from app.thermal.heat_index import calculate_heat_index
    from app.thermal.wbgt import calculate_wbgt
    from app.thermal.utci import calculate_utci
    from app.thermal.radiant_temperature import calculate_mrt

    hourly = raw.get("hourly", {})
    times: List[str] = hourly.get("time", [])
    temps: List[float] = hourly.get("temperature_2m", [])
    rhs: List[float] = hourly.get("relative_humidity_2m", [])
    winds: List[float] = hourly.get("wind_speed_10m", [])
    pressures: List[float] = hourly.get("surface_pressure", [])
    ghis: List[Optional[float]] = hourly.get("shortwave_radiation", [None] * len(times))
    directs: List[Optional[float]] = hourly.get("direct_radiation", [None] * len(times))
    diffuses: List[Optional[float]] = hourly.get("diffuse_radiation", [None] * len(times))
    dnis: List[Optional[float]] = hourly.get("direct_normal_irradiance", [None] * len(times))

    records = []
    for i, time_str in enumerate(times):
        try:
            ts = datetime.fromisoformat(time_str).replace(tzinfo=timezone.utc)
            ta = temps[i]
            rh = rhs[i]
            wind = winds[i]
            pressure = pressures[i]
            ghi = _safe(ghis[i] if i < len(ghis) else None)
            direct = _safe(directs[i] if i < len(directs) else None)
            diffuse = _safe(diffuses[i] if i < len(diffuses) else None)
            dni = _safe(dnis[i] if i < len(dnis) else None)

            # Skip rows with critical missing data
            if any(v is None for v in [ta, rh, wind, pressure]):
                continue

            # --- STEP 3 thermal calculations (not duplicated here) ---
            hi = calculate_heat_index(ta, rh)
            mrt = calculate_mrt(
                temperature_c=ta,
                shortwave_rad=ghi,
                direct_rad=direct,
                diffuse_rad=diffuse,
                dni=dni,
                latitude=lat,
                longitude=lon,
                timestamp=ts,
            )
            wbgt = calculate_wbgt(
                temperature_c=ta,
                relative_humidity=rh,
                wind_speed=wind,
                shortwave_rad=ghi if ghi is not None else 0.0,
                latitude=lat,
                longitude=lon,
                timestamp=ts,
                pressure_hpa=pressure,
            )
            utci = calculate_utci(
                temperature_c=ta,
                relative_humidity=rh,
                wind_speed=wind,
                mrt=mrt.get("value_c") if mrt else ta,
            )

            records.append({
                "timestamp": ts,
                "temp_c": ta,
                "rh_pct": rh,
                "wind_ms": wind,
                "pressure_hpa": pressure,
                "ghi_wm2": ghi,
                "direct_rad": direct,
                "diffuse_rad": diffuse,
                "dni": dni,
                "mrt_c": mrt.get("value_c") if mrt else None,
                # Thermal index values — None if NOT_APPLICABLE or error
                "heat_index_c": hi.get("value_c"),
                "wbgt_c": wbgt.get("value_c"),
                "utci_c": utci.get("value_c"),
                # Thermal index statuses (preserved for diagnostics)
                "hi_status": hi.get("status"),
                "wbgt_status": wbgt.get("status"),
                "utci_status": utci.get("status"),
            })
        except Exception as e:
            logger.warning(f"Skipping hour {time_str}: {e}")
            continue

    logger.info(f"Computed thermal history: {len(records)} valid hours out of {len(times)}")
    return records
