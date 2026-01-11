from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.extensions import db


class FileAsset(db.Model):
    __tablename__ = "files"
    __table_args__ = {"schema": "docs"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = db.Column(UUID(as_uuid=True), ForeignKey("core.project_revisions.id"), nullable=False)
    kind = db.Column(Text, nullable=False)
    storage_path = db.Column(Text, nullable=False)
    sha256 = db.Column(Text, nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())

    revision = db.relationship("ProjectRevision", backref="files")
