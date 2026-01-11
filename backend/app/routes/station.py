from __future__ import annotations

from flask import Blueprint, jsonify, request, g

from app.extensions import db
from app.models import Antenna, Feedline, ProjectRevision, Station, Transmitter
from app.utils.auth import require_auth


station_bp = Blueprint("station", __name__, url_prefix="/api/revisions")


def _get_revision_or_404(revision_id: str):
    revision = ProjectRevision.query.filter_by(id=revision_id).first()
    if not revision or revision.project.user_id != g.current_user.id:
        return None
    return revision


def _upsert(model, revision_id: str, data: dict):
    record = model.query.filter_by(revision_id=revision_id).first()
    if not record:
        record = model(revision_id=revision_id, **data)
        db.session.add(record)
    else:
        for key, value in data.items():
            setattr(record, key, value)
    db.session.commit()
    return record


@station_bp.patch("/<revision_id>/station")
@require_auth
def update_station(revision_id: str):
    revision = _get_revision_or_404(revision_id)
    if not revision:
        return jsonify({"error": "not_found"}), 404

    payload = request.get_json(force=True)
    data = {
        "tx_lat": payload.get("tx_lat"),
        "tx_lon": payload.get("tx_lon"),
        "ground_alt_m": payload.get("ground_alt_m"),
        "tower_height_agl_m": payload.get("tower_height_agl_m"),
        "frequency_mhz": payload.get("frequency_mhz"),
        "channel": payload.get("channel"),
        "bandwidth_khz": payload.get("bandwidth_khz"),
        "polarization": payload.get("polarization"),
        "datum": payload.get("datum", "SIRGAS2000"),
    }
    record = _upsert(Station, revision_id, data)
    return jsonify({"id": str(record.id)}), 200


@station_bp.patch("/<revision_id>/transmitter")
@require_auth
def update_transmitter(revision_id: str):
    revision = _get_revision_or_404(revision_id)
    if not revision:
        return jsonify({"error": "not_found"}), 404

    payload = request.get_json(force=True)
    data = {
        "tx_power_w": payload.get("tx_power_w"),
        "losses_internal_db": payload.get("losses_internal_db"),
        "notes": payload.get("notes"),
    }
    record = _upsert(Transmitter, revision_id, data)
    return jsonify({"id": str(record.id)}), 200


@station_bp.patch("/<revision_id>/feedline")
@require_auth
def update_feedline(revision_id: str):
    revision = _get_revision_or_404(revision_id)
    if not revision:
        return jsonify({"error": "not_found"}), 404

    payload = request.get_json(force=True)
    data = {
        "cable_type": payload.get("cable_type"),
        "length_m": payload.get("length_m"),
        "attn_db_per_100m": payload.get("attn_db_per_100m"),
        "connector_losses_db": payload.get("connector_losses_db"),
    }
    record = _upsert(Feedline, revision_id, data)
    return jsonify({"id": str(record.id)}), 200


@station_bp.patch("/<revision_id>/antenna")
@require_auth
def update_antenna(revision_id: str):
    revision = _get_revision_or_404(revision_id)
    if not revision:
        return jsonify({"error": "not_found"}), 404

    payload = request.get_json(force=True)
    data = {
        "gain_dbd": payload.get("gain_dbd"),
        "tilt_electrical_deg": payload.get("tilt_electrical_deg"),
        "tilt_mechanical_deg": payload.get("tilt_mechanical_deg"),
        "pattern_h_file_id": payload.get("pattern_h_file_id"),
        "pattern_v_file_id": payload.get("pattern_v_file_id"),
    }
    record = _upsert(Antenna, revision_id, data)
    return jsonify({"id": str(record.id)}), 200
