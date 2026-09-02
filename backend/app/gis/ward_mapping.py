import json
import os
from typing import Dict, Any, Optional
from app.core.config import settings

class WardMappingService:
    def __init__(self):
        self.wards = []
        data_path = os.path.join(os.path.dirname(__file__), "../../../data/KCH_wards.json")
        try:
            with open(data_path, "r") as f:
                data = json.load(f)
                self.wards = data if isinstance(data, list) else data.get("features", [])
        except Exception as e:
            print(f"Error loading KCH_wards.json: {e}")

    def get_all_wards_with_centroids(self):
        result = []
        for feature in self.wards:
            props = feature.get("properties", {})
            ward_no_str = props.get("Ward_No")
            if ward_no_str is None:
                continue
            ward_no = int(ward_no_str)
            ward_name = props.get("Ward_Name", f"Ward {ward_no}")
            
            geom = feature.get("geometry", {})
            geom_type = geom.get("type")
            coords = geom.get("coordinates", [])
            
            if geom_type == "Polygon" and coords:
                poly = coords[0]
            elif geom_type == "MultiPolygon" and coords:
                poly = coords[0][0]
            else:
                continue
                
            lons = [p[0] for p in poly]
            lats = [p[1] for p in poly]
            
            if not lons or not lats:
                continue
                
            c_lon = sum(lons) / len(lons)
            c_lat = sum(lats) / len(lats)
            
            result.append({
                "ward_no": ward_no,
                "ward_name": ward_name,
                "latitude": round(c_lat, 6),
                "longitude": round(c_lon, 6)
            })
        return sorted(result, key=lambda x: x["ward_no"])

    def get_boundary_status(self) -> str:
        return "CONFIGURED" if self.wards else "BOUNDARIES_NOT_CONFIGURED"

    def get_geometry(self, geographic_id: str, geographic_level: str) -> Optional[Dict[str, Any]]:
        """
        Returns the GeoJSON geometry for a given geographic_id.
        """
        if geographic_level != "WARD":
            return None
            
        for feature in self.wards:
            props = feature.get("properties", {})
            ward_no = props.get("Ward_No")
            if ward_no is not None:
                wid = f"W-{str(ward_no).zfill(2)}"
                if wid == geographic_id:
                    return feature.get("geometry")
        return None

    def _point_in_polygon(self, x, y, polygon):
        n = len(polygon)
        inside = False
        if n == 0:
            return False
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or x <= xinters:
                                inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def get_mock_wards_for_location(self, lat: float, lon: float) -> list:
        """
        Returns the real ward based on the spatial coordinate using KCH_wards.json.
        """
        for feature in self.wards:
            geom = feature.get("geometry", {})
            if not geom:
                continue
                
            geom_type = geom.get("type")
            coords = geom.get("coordinates", [])
            
            inside = False
            if geom_type == "Polygon":
                if coords and self._point_in_polygon(lon, lat, coords[0]):
                    inside = True
            elif geom_type == "MultiPolygon":
                for poly in coords:
                    if poly and self._point_in_polygon(lon, lat, poly[0]):
                        inside = True
                        break
            
            if inside:
                props = feature.get("properties", {})
                ward_no = props.get("Ward_No")
                if ward_no is not None:
                    wid = f"W-{str(ward_no).zfill(2)}"
                    return [{
                        "geographic_id": wid,
                        "name": props.get("Ward_Name", "Unknown Ward"),
                        "geographic_level": "WARD",
                    }]
        return []
