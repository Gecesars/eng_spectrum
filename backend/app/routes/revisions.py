from __future__ import annotations

from flask import Blueprint, jsonify, request, g

from app.extensions import db
from app.models import Project, ProjectRevision
from app.tasks.tasks import run_contour, run_interference, run_opea, run_rni
from app.utils.auth import require_auth


revisions_bp = Blueprint("revisions", __name__, url_prefix="/api")


@revisions_bp.post("/projects/<project_id>/revisions")
@require_auth
def create_revision(project_id: str):
    project = Project.query.filter_by(id=project_id, user_id=g.current_user.id).first()
    if not project:
        return jsonify({"error": "not_found"}), 404

    payload = request.get_json(force=True)
    label = payload.get("label", "Revision").strip()
    inputs_snapshot = payload.get("inputs_snapshot", {})

    revision = ProjectRevision(
        project_id=project.id,
        label=label,
        inputs_snapshot=inputs_snapshot,
    )
    db.session.add(revision)
    db.session.flush()

    project.current_revision_id = revision.id
    db.session.commit()

    return (
        jsonify(
            {
                "id": str(revision.id),
                "project_id": str(project.id),
                "label": revision.label,
                "created_at": revision.created_at.isoformat() if revision.created_at else None,
            }
        ),
        201,
    )


@revisions_bp.get("/revisions/<revision_id>")
@require_auth
def get_revision(revision_id: str):
    revision = ProjectRevision.query.filter_by(id=revision_id).first()
    if not revision or revision.project.user_id != g.current_user.id:
        return jsonify({"error": "not_found"}), 404

    return jsonify(
        {
            "id": str(revision.id),
            "project_id": str(revision.project_id),
            "label": revision.label,
            "created_at": revision.created_at.isoformat() if revision.created_at else None,
            "inputs_snapshot": revision.inputs_snapshot,
        }
    )


@revisions_bp.patch("/revisions/<revision_id>")
@require_auth
def update_revision(revision_id: str):
    revision = ProjectRevision.query.filter_by(id=revision_id).first()
    if not revision or revision.project.user_id != g.current_user.id:
        return jsonify({"error": "not_found"}), 404

    payload = request.get_json(force=True)
    inputs_snapshot = payload.get("inputs_snapshot")
    if inputs_snapshot is not None:
        revision.inputs_snapshot = inputs_snapshot

    db.session.commit()

    return jsonify({"message": "updated"}), 200


@revisions_bp.post("/revisions/<revision_id>/run")
@require_auth
def run_revision(revision_id: str):
    revision = ProjectRevision.query.filter_by(id=revision_id).first()
    if not revision or revision.project.user_id != g.current_user.id:
        return jsonify({"error": "not_found"}), 404

    payload = request.get_json(force=True)
    results = {}

    contour_args = payload.get("contour")
    if contour_args:
        results["contour"] = run_contour.delay(
            revision_id,
            float(contour_args.get("threshold_dbuvm", 54.0)),
            int(contour_args.get("step_deg", 5)),
            float(contour_args.get("step_km", 0.1)),
        ).get()

    if payload.get("interference"):
        results["interference"] = run_interference.delay(revision_id).get()

    rni_args = payload.get("rni")
    if rni_args:
        results["rni"] = run_rni.delay(
            revision_id,
            float(rni_args.get("s_limit_public", 10.0)),
            float(rni_args.get("s_limit_occ", 50.0)),
            float(rni_args.get("k_reflection", 2.56)),
        ).get()

    opea_args = payload.get("opea")
    if opea_args:
        results["opea"] = run_opea.delay(
            revision_id,
            opea_args.get("aerodrome_ref"),
            opea_args.get("aerodrome_lat"),
            opea_args.get("aerodrome_lon"),
        ).get()

    return jsonify({"message": "queued", "results": results}), 200
