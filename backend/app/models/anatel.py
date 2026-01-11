from __future__ import annotations

import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.extensions import db


class AnatelStation(db.Model):
    __tablename__ = "anatel_stations"
    __table_args__ = {"schema": "anatel"}

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    source = db.Column(Text, nullable=False)
    source_id = db.Column(Text, nullable=True)
    service = db.Column(Text, nullable=True)
    status = db.Column(Text, nullable=True)
    uf = db.Column(Text, nullable=True)
    municipio = db.Column(Text, nullable=True)
    cod_municipio = db.Column(Text, nullable=True)
    canal = db.Column(Text, nullable=True)
    frequencia_mhz = db.Column(Float, nullable=True)
    classe = db.Column(Text, nullable=True)
    erp_kw = db.Column(Float, nullable=True)
    altura_m = db.Column(Float, nullable=True)
    latitude = db.Column(Float, nullable=False)
    longitude = db.Column(Float, nullable=False)
    fistel = db.Column(Text, nullable=True)
    observacoes = db.Column(Text, nullable=True)
    pattern_dbd = db.Column(JSONB, nullable=True)
    limitacoes = db.Column(JSONB, nullable=True)
    geom = db.Column(Geometry("POINT", srid=4674, spatial_index=False), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())


class Aerodrome(db.Model):
    __tablename__ = "aerodromes"
    __table_args__ = {"schema": "anatel"}

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    source = db.Column(Text, nullable=False)
    name = db.Column(Text, nullable=True)
    icao = db.Column(Text, nullable=True)
    city = db.Column(Text, nullable=True)
    uf = db.Column(Text, nullable=True)
    latitude = db.Column(Float, nullable=False)
    longitude = db.Column(Float, nullable=False)
    kind = db.Column(Text, nullable=True)
    geom = db.Column(Geometry("POINT", srid=4674, spatial_index=False), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())


class ViabilityStudy(db.Model):
    __tablename__ = "viability_studies"
    __table_args__ = {"schema": "anatel"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    name = db.Column(Text, nullable=False)
    service_type = db.Column(Text, nullable=False)
    canal = db.Column(Text, nullable=True)
    frequencia_mhz = db.Column(Float, nullable=True)
    classe = db.Column(Text, nullable=True)
    erp_kw = db.Column(Float, nullable=True)
    altura_antena_m = db.Column(Float, nullable=True)
    haat_m = db.Column(Float, nullable=True)
    polarizacao = db.Column(Text, nullable=True)
    latitude = db.Column(Float, nullable=False)
    longitude = db.Column(Float, nullable=False)
    municipio = db.Column(Text, nullable=True)
    uf = db.Column(Text, nullable=True)
    parametros_json = db.Column(JSONB, nullable=False, default=dict)
    resultado_json = db.Column(JSONB, nullable=False, default=dict)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = db.relationship("User", backref="viability_studies")
