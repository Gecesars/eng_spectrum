from __future__ import annotations

import math
from dataclasses import dataclass

from geoalchemy2.elements import WKTElement

from app.extensions import db
from app.models import RNIAssessment, RNIZone, ProjectRevision, Station
from app.services.contour import erp_dbw
from app.utils.geo import GeoPoint, build_polygon_wkt, destination_point, generate_radials


@dataclass(frozen=True)
class RNIResult:
    assessment: RNIAssessment
    zones: list[RNIZone]


def calc_eirp_w(revision: ProjectRevision) -> float:
    erp_dbw_value = erp_dbw(
        revision.transmitter[0] if revision.transmitter else None,
        revision.antenna[0] if revision.antenna else None,
        revision.feedline[0] if revision.feedline else None,
    )
    if erp_dbw_value == -math.inf:
        return 0.0
    return 10 ** (erp_dbw_value / 10.0)


def calc_r_compliance_far_field(eirp_w: float, k: float, s_lim: float) -> float:
    if eirp_w <= 0 or s_lim <= 0:
        return 0.0
    return math.sqrt((30.0 * eirp_w * k) / s_lim)


def _build_circle_polygon(lat: float, lon: float, radius_m: float) -> str:
    points: list[GeoPoint] = []
    for azimuth in generate_radials(5):
        points.append(destination_point(lat, lon, azimuth, radius_m / 1000.0))
    return build_polygon_wkt(points)


def run_rni_assessment(
    revision: ProjectRevision,
    s_limit_w_m2_public: float,
    s_limit_w_m2_occ: float,
    k_reflection: float = 2.56,
) -> RNIResult:
    station: Station | None = revision.station[0] if revision.station else None
    if not station:
        raise ValueError("Station data is required for RNI assessment")

    eirp_w = calc_eirp_w(revision)
    r_public_m = calc_r_compliance_far_field(eirp_w, k_reflection, s_limit_w_m2_public)
    r_occ_m = calc_r_compliance_far_field(eirp_w, k_reflection, s_limit_w_m2_occ)

    assessment = RNIAssessment(
        revision_id=revision.id,
        eirp_w=eirp_w,
        k_reflection=k_reflection,
        s_limit_w_m2_public=s_limit_w_m2_public,
        s_limit_w_m2_occ=s_limit_w_m2_occ,
        r_public_m=r_public_m,
        r_occ_m=r_occ_m,
        notes=None,
    )
    db.session.add(assessment)
    db.session.flush()

    public_poly = _build_circle_polygon(station.tx_lat, station.tx_lon, r_public_m)
    occ_poly = _build_circle_polygon(station.tx_lat, station.tx_lon, r_occ_m)

    zones = [
        RNIZone(
            rni_id=assessment.id,
            zone_kind="public",
            geom=WKTElement(public_poly, srid=int(revision.inputs_snapshot.get("srid", 4674))),
        ),
        RNIZone(
            rni_id=assessment.id,
            zone_kind="occupational",
            geom=WKTElement(occ_poly, srid=int(revision.inputs_snapshot.get("srid", 4674))),
        ),
    ]

    for zone in zones:
        db.session.add(zone)

    db.session.commit()

    return RNIResult(assessment=assessment, zones=zones)
