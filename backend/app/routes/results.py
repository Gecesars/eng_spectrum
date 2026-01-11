from __future__ import annotations

from flask import Blueprint, jsonify, g

from app.models import Contour, ContourPoint, InterferenceCase, InterferenceTestPoint, OPEAAssessment, ProjectRevision, RNIAssessment, RNIZone
from app.utils.auth import require_auth


results_bp = Blueprint("results", __name__, url_prefix="/api/revisions")


def _get_revision_or_404(revision_id: str):
    revision = ProjectRevision.query.filter_by(id=revision_id).first()
    if not revision or revision.project.user_id != g.current_user.id:
        return None
    return revision


@results_bp.get("/<revision_id>/contour")
@require_auth
def get_contour(revision_id: str):
    revision = _get_revision_or_404(revision_id)
    if not revision:
        return jsonify({"error": "not_found"}), 404

    contour = Contour.query.filter_by(revision_id=revision.id).order_by(Contour.id).first()
    if not contour:
        return jsonify({"error": "not_found"}), 404

    points = ContourPoint.query.filter_by(contour_id=contour.id).order_by(ContourPoint.order_idx).all()
    return jsonify(
        {
            "id": str(contour.id),
            "threshold_dbuvm": contour.threshold_dbuvm,
            "method": contour.method,
            "points": [
                {
                    "azimuth_deg": p.azimuth_deg,
                    "distance_km": p.distance_km,
                    "lat": p.lat,
                    "lon": p.lon,
                }
                for p in points
            ],
        }
    )


@results_bp.get("/<revision_id>/interference")
@require_auth
def get_interference(revision_id: str):
    revision = _get_revision_or_404(revision_id)
    if not revision:
        return jsonify({"error": "not_found"}), 404

    cases = InterferenceCase.query.filter_by(revision_id=revision.id).all()
    payload = []
    for case in cases:
        points = InterferenceTestPoint.query.filter_by(case_id=case.id).all()
        payload.append(
            {
                "id": str(case.id),
                "relationship": case.relationship,
                "du_required_db": case.du_required_db,
                "points": [
                    {
                        "d_dbuvm": p.d_dbuvm,
                        "u_dbuvm": p.u_dbuvm,
                        "margin_db": p.margin_db,
                        "passed": p.passed,
                    }
                    for p in points
                ],
            }
        )
    return jsonify(payload)


@results_bp.get("/<revision_id>/rni")
@require_auth
def get_rni(revision_id: str):
    revision = _get_revision_or_404(revision_id)
    if not revision:
        return jsonify({"error": "not_found"}), 404

    assessment = RNIAssessment.query.filter_by(revision_id=revision.id).order_by(RNIAssessment.id).first()
    if not assessment:
        return jsonify({"error": "not_found"}), 404

    zones = RNIZone.query.filter_by(rni_id=assessment.id).all()
    return jsonify(
        {
            "id": str(assessment.id),
            "eirp_w": assessment.eirp_w,
            "r_public_m": assessment.r_public_m,
            "r_occ_m": assessment.r_occ_m,
            "zones": [
                {
                    "zone_kind": zone.zone_kind,
                }
                for zone in zones
            ],
        }
    )


@results_bp.get("/<revision_id>/opea")
@require_auth
def get_opea(revision_id: str):
    revision = _get_revision_or_404(revision_id)
    if not revision:
        return jsonify({"error": "not_found"}), 404

    assessment = OPEAAssessment.query.filter_by(revision_id=revision.id).order_by(OPEAAssessment.id).first()
    if not assessment:
        return jsonify({"error": "not_found"}), 404

    return jsonify(
        {
            "id": str(assessment.id),
            "within_20km": assessment.within_20km,
            "result": assessment.result,
        }
    )
