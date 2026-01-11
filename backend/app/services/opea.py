from __future__ import annotations

from dataclasses import dataclass

from app.extensions import db
from app.models import OPEAAssessment, ProjectRevision, Station
from app.utils.geo import distance_km


@dataclass(frozen=True)
class OPEAResult:
    assessment: OPEAAssessment


def check_within_20km_aerodrome(
    station_lat: float,
    station_lon: float,
    aerodrome_lat: float,
    aerodrome_lon: float,
) -> bool:
    return distance_km(station_lat, station_lon, aerodrome_lat, aerodrome_lon) <= 20.0


def run_opea_assessment(
    revision: ProjectRevision,
    aerodrome_ref: str | None = None,
    aerodrome_lat: float | None = None,
    aerodrome_lon: float | None = None,
) -> OPEAResult:
    station: Station | None = revision.station[0] if revision.station else None
    if not station:
        raise ValueError("Station data is required for OPEA assessment")

    within_20km = False
    if aerodrome_lat is not None and aerodrome_lon is not None:
        within_20km = check_within_20km_aerodrome(
            station.tx_lat,
            station.tx_lon,
            aerodrome_lat,
            aerodrome_lon,
        )

    result = "ok" if not within_20km else "needs_shadow_study"

    assessment = OPEAAssessment(
        revision_id=revision.id,
        aerodrome_ref=aerodrome_ref,
        within_20km=within_20km,
        result=result,
        notes=None,
    )
    db.session.add(assessment)
    db.session.commit()

    return OPEAResult(assessment=assessment)
