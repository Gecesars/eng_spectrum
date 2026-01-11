from __future__ import annotations

from flask import Blueprint, current_app, jsonify, g

import hashlib

from app.extensions import db
from app.models import Contour, FileAsset, ProjectRevision
from app.services.export import export_kml, export_mosaico_txt, export_shapefile
from app.utils.auth import require_auth


export_bp = Blueprint("export", __name__, url_prefix="/api/revisions")


def _get_revision_or_404(revision_id: str):
    revision = ProjectRevision.query.filter_by(id=revision_id).first()
    if not revision or revision.project.user_id != g.current_user.id:
        return None
    return revision


def _get_contour(revision_id: str):
    return Contour.query.filter_by(revision_id=revision_id).order_by(Contour.id).first()


def _save_asset(revision_id: str, kind: str, path: str):
    sha256 = ""
    try:
        with open(path, "rb") as handle:
            sha256 = hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        sha256 = ""
    asset = FileAsset(
        revision_id=revision_id,
        kind=kind,
        storage_path=path,
        sha256=sha256,
    )
    db.session.add(asset)
    db.session.commit()
    return asset


@export_bp.post("/<revision_id>/export/kml")
@require_auth
def export_kml_route(revision_id: str):
    revision = _get_revision_or_404(revision_id)
    if not revision:
        return jsonify({"error": "not_found"}), 404

    contour = _get_contour(revision.id)
    if not contour:
        return jsonify({"error": "contour_required"}), 400

    result = export_kml(contour, current_app.config["EXPORT_DIR"])
    asset = _save_asset(revision.id, result.kind, result.path)

    return jsonify({"path": result.path, "asset_id": str(asset.id)}), 201


@export_bp.post("/<revision_id>/export/shp")
@require_auth
def export_shp_route(revision_id: str):
    revision = _get_revision_or_404(revision_id)
    if not revision:
        return jsonify({"error": "not_found"}), 404

    contour = _get_contour(revision.id)
    if not contour:
        return jsonify({"error": "contour_required"}), 400

    result = export_shapefile(contour, current_app.config["EXPORT_DIR"])
    asset = _save_asset(revision.id, result.kind, result.path)

    return jsonify({"path": result.path, "asset_id": str(asset.id)}), 201


@export_bp.post("/<revision_id>/export/mosaico-txt")
@require_auth
def export_mosaico_route(revision_id: str):
    revision = _get_revision_or_404(revision_id)
    if not revision:
        return jsonify({"error": "not_found"}), 404

    contour = _get_contour(revision.id)
    if not contour:
        return jsonify({"error": "contour_required"}), 400

    result = export_mosaico_txt(contour, current_app.config["EXPORT_DIR"])
    asset = _save_asset(revision.id, result.kind, result.path)

    return jsonify({"path": result.path, "asset_id": str(asset.id)}), 201


@export_bp.post("/<revision_id>/export/report-pdf")
@require_auth
def export_report_route(revision_id: str):
    revision = _get_revision_or_404(revision_id)
    if not revision:
        return jsonify({"error": "not_found"}), 404

    return jsonify({"error": "not_implemented"}), 501
