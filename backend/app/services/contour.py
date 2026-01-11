from __future__ import annotations

import math
from dataclasses import dataclass

from geoalchemy2.elements import WKTElement

from app.extensions import db
from app.models import Antenna, Contour, ContourPoint, Feedline, ProjectRevision, Station, Transmitter
from app.utils.geo import GeoPoint, build_polygon_wkt, destination_point, generate_radials


@dataclass(frozen=True)
class ContourResult:
    contour: Contour
    points: list[ContourPoint]


def _db_to_linear(db_value: float) -> float:
    return 10 ** (db_value / 10.0)


def _linear_to_db(linear: float) -> float:
    if linear <= 0:
        return -math.inf
    return 10 * math.log10(linear)


def _effective_losses_db(feedline: Feedline | None, transmitter: Transmitter | None) -> float:
    losses = 0.0
    if transmitter and transmitter.losses_internal_db:
        losses += transmitter.losses_internal_db
    if feedline:
        if feedline.length_m and feedline.attn_db_per_100m:
            losses += feedline.length_m * feedline.attn_db_per_100m / 100.0
        if feedline.connector_losses_db:
            losses += feedline.connector_losses_db
    return losses


def erp_dbw(transmitter: Transmitter | None, antenna: Antenna | None, feedline: Feedline | None) -> float:
    if not transmitter:
        return -math.inf
    power_w = transmitter.tx_power_w
    if power_w <= 0:
        return -math.inf
    power_dbw = _linear_to_db(power_w)
    gain_dbd = antenna.gain_dbd if antenna and antenna.gain_dbd is not None else 0.0
    losses_db = _effective_losses_db(feedline, transmitter)
    return power_dbw + gain_dbd - losses_db


def field_strength_dbuvm(erp_dbw_value: float, distance_km: float) -> float:
    if distance_km <= 0:
        return math.inf
    erp_kw = _db_to_linear(erp_dbw_value) / 1000.0
    if erp_kw <= 0:
        return -math.inf
    return 106.92 + 10 * math.log10(erp_kw) - 20 * math.log10(distance_km)


def compute_contour(
    revision: ProjectRevision,
    threshold_dbuvm: float,
    step_deg: int = 5,
    step_km: float = 0.1,
    max_distance_km: float = 200.0,
) -> ContourResult:
    station: Station | None = revision.station[0] if revision.station else None
    if not station:
        raise ValueError("Station data is required to compute contour")

    transmitter = revision.transmitter[0] if revision.transmitter else None
    feedline = revision.feedline[0] if revision.feedline else None
    antenna = revision.antenna[0] if revision.antenna else None

    erp = erp_dbw(transmitter, antenna, feedline)
    radials = generate_radials(step_deg)

    contour_points: list[ContourPoint] = []
    poly_points: list[GeoPoint] = []

    for idx, azimuth in enumerate(radials):
        farthest_distance_km = 0.0
        farthest_point = destination_point(station.tx_lat, station.tx_lon, azimuth, 0.0)

        distance_km = step_km
        while distance_km <= max_distance_km:
            e_dbuvm = field_strength_dbuvm(erp, distance_km)
            if e_dbuvm >= threshold_dbuvm:
                farthest_distance_km = distance_km
                farthest_point = destination_point(station.tx_lat, station.tx_lon, azimuth, distance_km)
            distance_km += step_km

        contour_points.append(
            ContourPoint(
                azimuth_deg=azimuth,
                distance_km=round(farthest_distance_km, 4),
                lat=farthest_point.lat,
                lon=farthest_point.lon,
                order_idx=idx,
            )
        )
        poly_points.append(farthest_point)

    polygon_wkt = build_polygon_wkt(poly_points)
    contour = Contour(
        revision_id=revision.id,
        contour_kind="protected",
        threshold_dbuvm=threshold_dbuvm,
        method="hybrid",
        geom=WKTElement(
            polygon_wkt,
            srid=int(revision.inputs_snapshot.get("srid", 4674)) if revision.inputs_snapshot else 4674,
        ),
        metadata_json={
            "step_deg": step_deg,
            "step_km": step_km,
            "max_distance_km": max_distance_km,
            "erp_dbw": erp,
            "threshold_dbuvm": threshold_dbuvm,
        },
    )

    db.session.add(contour)
    db.session.flush()

    for point in contour_points:
        point.contour_id = contour.id
        db.session.add(point)

    db.session.commit()

    return ContourResult(contour=contour, points=contour_points)
