from __future__ import annotations

from flask import Blueprint, jsonify, request, g
from geoalchemy2 import Geography
from sqlalchemy import func

from app.extensions import db
from app.models import Aerodrome, AnatelStation, ViabilityStudy
from app.utils.auth import require_auth


anatel_bp = Blueprint("anatel", __name__, url_prefix="/api/anatel")


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _point(lon: float, lat: float):
    return func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4674)


@anatel_bp.get("/stations")
@require_auth
def list_stations():
    lat = _parse_float(request.args.get("lat"))
    lon = _parse_float(request.args.get("lon"))
    radius_km = _parse_float(request.args.get("radius_km")) or 50.0
    service = request.args.get("service")
    limit = int(request.args.get("limit", "200"))

    query = AnatelStation.query
    if service:
        query = query.filter(AnatelStation.service == service)

    if lat is not None and lon is not None:
        center = _point(lon, lat)
        query = query.filter(
            func.ST_DWithin(
                AnatelStation.geom.cast(Geography),
                center.cast(Geography),
                radius_km * 1000.0,
            )
        )

    stations = query.limit(limit).all()
    return jsonify(
        [
            {
                "id": station.id,
                "service": station.service,
                "status": station.status,
                "uf": station.uf,
                "municipio": station.municipio,
                "canal": station.canal,
                "frequencia_mhz": station.frequencia_mhz,
                "classe": station.classe,
                "erp_kw": station.erp_kw,
                "altura_m": station.altura_m,
                "lat": station.latitude,
                "lon": station.longitude,
                "observacoes": station.observacoes,
            }
            for station in stations
        ]
    )


@anatel_bp.get("/aerodromes")
@require_auth
def list_aerodromes():
    lat = _parse_float(request.args.get("lat"))
    lon = _parse_float(request.args.get("lon"))
    radius_km = _parse_float(request.args.get("radius_km")) or 50.0
    limit = int(request.args.get("limit", "200"))

    query = Aerodrome.query
    if lat is not None and lon is not None:
        center = _point(lon, lat)
        query = query.filter(
            func.ST_DWithin(
                Aerodrome.geom.cast(Geography),
                center.cast(Geography),
                radius_km * 1000.0,
            )
        )

    aerodromes = query.limit(limit).all()
    return jsonify(
        [
            {
                "id": aero.id,
                "name": aero.name,
                "icao": aero.icao,
                "city": aero.city,
                "uf": aero.uf,
                "kind": aero.kind,
                "lat": aero.latitude,
                "lon": aero.longitude,
            }
            for aero in aerodromes
        ]
    )


@anatel_bp.post("/studies")
@require_auth
def create_study():
    payload = request.get_json(force=True)
    name = payload.get("name", "").strip()
    service_type = payload.get("service_type", "").strip()
    latitude = _parse_float(payload.get("latitude"))
    longitude = _parse_float(payload.get("longitude"))

    if not name or not service_type or latitude is None or longitude is None:
        return jsonify({"error": "name_service_lat_lon_required"}), 400

    study = ViabilityStudy(
        user_id=g.current_user.id,
        name=name,
        service_type=service_type,
        canal=payload.get("canal"),
        frequencia_mhz=_parse_float(payload.get("frequencia_mhz")),
        classe=payload.get("classe"),
        erp_kw=_parse_float(payload.get("erp_kw")),
        altura_antena_m=_parse_float(payload.get("altura_antena_m")),
        haat_m=_parse_float(payload.get("haat_m")),
        polarizacao=payload.get("polarizacao"),
        latitude=latitude,
        longitude=longitude,
        municipio=payload.get("municipio"),
        uf=payload.get("uf"),
        parametros_json=payload.get("parametros_json", {}),
        resultado_json=payload.get("resultado_json", {}),
    )

    db.session.add(study)
    db.session.commit()

    return jsonify({"id": str(study.id)}), 201


@anatel_bp.get("/studies")
@require_auth
def list_studies():
    studies = ViabilityStudy.query.filter_by(user_id=g.current_user.id).order_by(ViabilityStudy.created_at.desc()).all()
    return jsonify(
        [
            {
                "id": str(study.id),
                "name": study.name,
                "service_type": study.service_type,
                "created_at": study.created_at.isoformat() if study.created_at else None,
            }
            for study in studies
        ]
    )


@anatel_bp.get("/studies/<study_id>")
@require_auth
def get_study(study_id: str):
    study = ViabilityStudy.query.filter_by(id=study_id, user_id=g.current_user.id).first()
    if not study:
        return jsonify({"error": "not_found"}), 404

    return jsonify(
        {
            "id": str(study.id),
            "name": study.name,
            "service_type": study.service_type,
            "canal": study.canal,
            "frequencia_mhz": study.frequencia_mhz,
            "classe": study.classe,
            "erp_kw": study.erp_kw,
            "altura_antena_m": study.altura_antena_m,
            "haat_m": study.haat_m,
            "polarizacao": study.polarizacao,
            "latitude": study.latitude,
            "longitude": study.longitude,
            "municipio": study.municipio,
            "uf": study.uf,
            "parametros_json": study.parametros_json,
            "resultado_json": study.resultado_json,
        }
    )
