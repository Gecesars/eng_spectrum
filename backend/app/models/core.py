from __future__ import annotations

import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.extensions import db


class Project(db.Model):
    __tablename__ = "projects"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    name = db.Column(Text, nullable=False)
    service_type = db.Column(Text, nullable=False)
    status = db.Column(Text, nullable=False, default="draft")
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    current_revision_id = db.Column(UUID(as_uuid=True), nullable=True)

    user = db.relationship("User", backref="projects")


class ProjectRevision(db.Model):
    __tablename__ = "project_revisions"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), ForeignKey("core.projects.id"), nullable=False)
    label = db.Column(Text, nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    inputs_snapshot = db.Column(JSONB, nullable=False, default=dict)

    project = db.relationship("Project", backref="revisions")


class Station(db.Model):
    __tablename__ = "station"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = db.Column(UUID(as_uuid=True), ForeignKey("core.project_revisions.id"), nullable=False)
    tx_lat = db.Column(Float, nullable=False)
    tx_lon = db.Column(Float, nullable=False)
    ground_alt_m = db.Column(Float, nullable=True)
    tower_height_agl_m = db.Column(Float, nullable=True)
    frequency_mhz = db.Column(Float, nullable=True)
    channel = db.Column(Integer, nullable=True)
    bandwidth_khz = db.Column(Integer, nullable=True)
    polarization = db.Column(Text, nullable=True)
    datum = db.Column(Text, nullable=False, default="SIRGAS2000")

    revision = db.relationship("ProjectRevision", backref="station")


class Transmitter(db.Model):
    __tablename__ = "transmitter"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = db.Column(UUID(as_uuid=True), ForeignKey("core.project_revisions.id"), nullable=False)
    tx_power_w = db.Column(Float, nullable=False)
    losses_internal_db = db.Column(Float, nullable=True)
    notes = db.Column(Text, nullable=True)

    revision = db.relationship("ProjectRevision", backref="transmitter")


class Feedline(db.Model):
    __tablename__ = "feedline"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = db.Column(UUID(as_uuid=True), ForeignKey("core.project_revisions.id"), nullable=False)
    cable_type = db.Column(Text, nullable=True)
    length_m = db.Column(Float, nullable=True)
    attn_db_per_100m = db.Column(Float, nullable=True)
    connector_losses_db = db.Column(Float, nullable=True)

    revision = db.relationship("ProjectRevision", backref="feedline")


class Antenna(db.Model):
    __tablename__ = "antenna"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = db.Column(UUID(as_uuid=True), ForeignKey("core.project_revisions.id"), nullable=False)
    gain_dbd = db.Column(Float, nullable=True)
    tilt_electrical_deg = db.Column(Float, nullable=True)
    tilt_mechanical_deg = db.Column(Float, nullable=True)
    pattern_h_file_id = db.Column(UUID(as_uuid=True), nullable=True)
    pattern_v_file_id = db.Column(UUID(as_uuid=True), nullable=True)

    revision = db.relationship("ProjectRevision", backref="antenna")


class InterferenceCase(db.Model):
    __tablename__ = "interference_cases"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = db.Column(UUID(as_uuid=True), ForeignKey("core.project_revisions.id"), nullable=False)
    victim_station_ref = db.Column(Text, nullable=False)
    relationship = db.Column(Text, nullable=False)
    du_required_db = db.Column(Float, nullable=False)
    notes = db.Column(Text, nullable=True)

    revision = db.relationship("ProjectRevision", backref="interference_cases")


class RNIAssessment(db.Model):
    __tablename__ = "rni_assessments"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = db.Column(UUID(as_uuid=True), ForeignKey("core.project_revisions.id"), nullable=False)
    eirp_w = db.Column(Float, nullable=False)
    k_reflection = db.Column(Float, nullable=False)
    s_limit_w_m2_public = db.Column(Float, nullable=False)
    s_limit_w_m2_occ = db.Column(Float, nullable=False)
    r_public_m = db.Column(Float, nullable=False)
    r_occ_m = db.Column(Float, nullable=False)
    notes = db.Column(Text, nullable=True)

    revision = db.relationship("ProjectRevision", backref="rni_assessments")


class OPEAAssessment(db.Model):
    __tablename__ = "opea_assessments"
    __table_args__ = {"schema": "core"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = db.Column(UUID(as_uuid=True), ForeignKey("core.project_revisions.id"), nullable=False)
    aerodrome_ref = db.Column(Text, nullable=True)
    within_20km = db.Column(Boolean, nullable=False, default=False)
    result = db.Column(Text, nullable=False)
    notes = db.Column(Text, nullable=True)

    revision = db.relationship("ProjectRevision", backref="opea_assessments")
