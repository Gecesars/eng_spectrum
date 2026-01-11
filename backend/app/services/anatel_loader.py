from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET

from geoalchemy2.elements import WKTElement

from app.extensions import db
from app.models import Aerodrome, AnatelStation


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_pipe_list(value: str | None) -> list[float] | None:
    if not value:
        return None
    parts = [p for p in value.split("|") if p != ""]
    if not parts:
        return None
    parsed = []
    for part in parts:
        try:
            parsed.append(float(part))
        except ValueError:
            parsed.append(0.0)
    return parsed


def import_anatel_xml(path: str, truncate: bool = False) -> int:
    if truncate:
        AnatelStation.query.delete()
        db.session.commit()

    total = 0
    source = os.path.basename(path)

    for event, elem in ET.iterparse(path, events=("end",)):
        if elem.tag != "row":
            continue
        attrs = elem.attrib
        lat = _parse_float(attrs.get("Latitude"))
        lon = _parse_float(attrs.get("Longitude"))
        if lat is None or lon is None:
            elem.clear()
            continue

        station = AnatelStation(
            source=source,
            source_id=attrs.get("id") or attrs.get("IdtPlanoBasico"),
            service=attrs.get("Servico"),
            status=attrs.get("Status"),
            uf=attrs.get("UF"),
            municipio=attrs.get("Municipio"),
            cod_municipio=attrs.get("CodMunicipio"),
            canal=attrs.get("Canal"),
            frequencia_mhz=_parse_float(attrs.get("Frequencia")),
            classe=attrs.get("Classe"),
            erp_kw=_parse_float(attrs.get("ERP")),
            altura_m=_parse_float(attrs.get("Altura")),
            latitude=lat,
            longitude=lon,
            fistel=attrs.get("Fistel"),
            observacoes=attrs.get("Observacoes"),
            pattern_dbd=_parse_pipe_list(attrs.get("PadraoAntena_dBd")),
            limitacoes=_parse_pipe_list(attrs.get("Limitacoes")),
            geom=WKTElement(f"POINT({lon} {lat})", srid=4674),
        )
        db.session.add(station)
        total += 1

        if total % 1000 == 0:
            db.session.commit()
        elem.clear()

    db.session.commit()
    return total


def _find_value(record: dict, keys: tuple[str, ...]):
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def import_aerodromes_json(path: str, truncate: bool = False) -> int:
    if truncate:
        Aerodrome.query.delete()
        db.session.commit()

    source = os.path.basename(path)
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, dict):
        records = list(data.values())
    else:
        records = data

    total = 0
    for record in records:
        lat = _find_value(record, ("lat", "latitude", "LAT", "Latitude"))
        lon = _find_value(record, ("lon", "longitude", "LON", "Longitude"))
        if lat is None or lon is None:
            continue
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except ValueError:
            continue

        aerodrome = Aerodrome(
            source=source,
            name=_find_value(record, ("nome", "name", "Nome")),
            icao=_find_value(record, ("icao", "ICAO")),
            city=_find_value(record, ("municipio", "cidade", "city", "Municipio")),
            uf=_find_value(record, ("uf", "UF")),
            kind=_find_value(record, ("tipo", "kind")),
            latitude=lat_f,
            longitude=lon_f,
            geom=WKTElement(f"POINT({lon_f} {lat_f})", srid=4674),
        )
        db.session.add(aerodrome)
        total += 1

        if total % 1000 == 0:
            db.session.commit()

    db.session.commit()
    return total
