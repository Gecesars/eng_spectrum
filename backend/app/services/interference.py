from __future__ import annotations

from dataclasses import dataclass

from geoalchemy2.elements import WKTElement

from app.extensions import db
from app.models import Contour, ContourPoint, InterferenceCase, InterferenceTestPoint, ProjectRevision, Station
from app.services.contour import erp_dbw, field_strength_dbuvm
from app.utils.geo import distance_km


@dataclass(frozen=True)
class InterferenceResult:
    case: InterferenceCase
    points: list[InterferenceTestPoint]
    passed: bool


def run_interference_case(revision: ProjectRevision, case: InterferenceCase) -> InterferenceResult:
    contour = (
        Contour.query.filter_by(revision_id=revision.id, contour_kind="protected")
        .order_by(Contour.id)
        .first()
    )
    if not contour:
        raise ValueError("Protected contour is required for interference analysis")

    station: Station | None = revision.station[0] if revision.station else None
    if not station:
        raise ValueError("Station data is required for interference analysis")

    points = ContourPoint.query.filter_by(contour_id=contour.id).order_by(ContourPoint.order_idx).all()
    if not points:
        raise ValueError("Contour points are required for interference analysis")

    erp = erp_dbw(
        revision.transmitter[0] if revision.transmitter else None,
        revision.antenna[0] if revision.antenna else None,
        revision.feedline[0] if revision.feedline else None,
    )

    test_points: list[InterferenceTestPoint] = []
    passed = True

    for point in points:
        d_dbuvm = contour.threshold_dbuvm
        distance = distance_km(station.tx_lat, station.tx_lon, point.lat, point.lon)
        u_dbuvm = field_strength_dbuvm(erp, distance)
        margin_db = (d_dbuvm - u_dbuvm) - case.du_required_db
        point_passed = margin_db >= 0
        passed = passed and point_passed

        test_points.append(
            InterferenceTestPoint(
                case_id=case.id,
                geom=WKTElement(f"POINT({point.lon} {point.lat})", srid=contour.geom.srid or 4674),
                d_dbuvm=d_dbuvm,
                u_dbuvm=u_dbuvm,
                margin_db=margin_db,
                passed=point_passed,
            )
        )

    for test_point in test_points:
        db.session.add(test_point)

    db.session.commit()

    return InterferenceResult(case=case, points=test_points, passed=passed)
