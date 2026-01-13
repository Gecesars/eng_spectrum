from __future__ import annotations

import os
import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from geoalchemy2 import Geometry

from app.extensions import db


SRID = int(os.getenv("SRID", "4674"))


class GISContour(db.Model):
    __tablename__ = "contours"
    __table_args__ = {"schema": "gis", "extend_existing": True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = db.Column(UUID(as_uuid=True), ForeignKey("core.project_revisions.id"), nullable=False)
    contour_kind = db.Column(Text, nullable=False)
    threshold_dbuvm = db.Column(Float, nullable=False)
    method = db.Column(Text, nullable=False)
    geom = db.Column(Geometry("POLYGON", srid=SRID, spatial_index=False), nullable=False)
    metadata_json = db.Column("metadata", JSONB, nullable=True, default=dict)

    revision = db.relationship("ProjectRevision", backref="contours")


class ContourPoint(db.Model):
    __tablename__ = "contour_points"
    __table_args__ = {"schema": "gis"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contour_id = db.Column(UUID(as_uuid=True), ForeignKey("gis.contours.id"), nullable=False)
    azimuth_deg = db.Column(Integer, nullable=False)
    distance_km = db.Column(Float, nullable=False)
    lat = db.Column(Float, nullable=False)
    lon = db.Column(Float, nullable=False)
    order_idx = db.Column(Integer, nullable=False)

    contour = db.relationship("GISContour", backref="points")


class InterferenceTestPoint(db.Model):
    __tablename__ = "interference_testpoints"
    __table_args__ = {"schema": "gis"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = db.Column(UUID(as_uuid=True), ForeignKey("core.interference_cases.id"), nullable=False)
    geom = db.Column(Geometry("POINT", srid=SRID, spatial_index=False), nullable=False)
    d_dbuvm = db.Column(Float, nullable=False)
    u_dbuvm = db.Column(Float, nullable=False)
    margin_db = db.Column(Float, nullable=False)
    passed = db.Column(Boolean, nullable=False)

    interference_case = db.relationship("InterferenceCase", backref="test_points")


class RNIZone(db.Model):
    __tablename__ = "rni_zones"
    __table_args__ = {"schema": "gis"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rni_id = db.Column(UUID(as_uuid=True), ForeignKey("core.rni_assessments.id"), nullable=False)
    zone_kind = db.Column(Text, nullable=False)
    geom = db.Column(Geometry("POLYGON", srid=SRID, spatial_index=False), nullable=False)

    rni = db.relationship("RNIAssessment", backref="zones")


class RNICriticalArea(db.Model):
    __tablename__ = "rni_critical_areas"
    __table_args__ = {"schema": "gis"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rni_id = db.Column(UUID(as_uuid=True), ForeignKey("core.rni_assessments.id"), nullable=False)
    kind = db.Column(Text, nullable=False)
    geom = db.Column(Geometry("POLYGON", srid=SRID, spatial_index=False), nullable=False)
    within_50m = db.Column(Boolean, nullable=False, default=False)

    rni = db.relationship("RNIAssessment", backref="critical_areas")
