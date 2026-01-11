from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from geographiclib.geodesic import Geodesic


@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lon: float


WGS84 = Geodesic.WGS84


def generate_radials(step_deg: int = 5) -> list[int]:
    if step_deg <= 0 or 360 % step_deg != 0:
        raise ValueError("step_deg must be a positive divisor of 360")
    return list(range(0, 360, step_deg))


def destination_point(lat: float, lon: float, azimuth_deg: float, distance_km: float) -> GeoPoint:
    result = WGS84.Direct(lat, lon, azimuth_deg, distance_km * 1000.0)
    return GeoPoint(lat=result["lat2"], lon=result["lon2"])


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    result = WGS84.Inverse(lat1, lon1, lat2, lon2)
    return result["s12"] / 1000.0


def build_polygon_wkt(points: Iterable[GeoPoint]) -> str:
    coords = [(p.lon, p.lat) for p in points]
    if not coords:
        raise ValueError("points must not be empty")
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    coord_str = ", ".join(f"{lon} {lat}" for lon, lat in coords)
    return f"POLYGON(({coord_str}))"
