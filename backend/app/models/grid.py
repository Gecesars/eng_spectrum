from __future__ import annotations

from sqlalchemy import Integer, LargeBinary, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions import db


class FieldTile(db.Model):
    __tablename__ = "field_tiles"
    __table_args__ = (
        db.PrimaryKeyConstraint("revision_id", "layer", "z", "x", "y"),
        db.Index("idx_field_tiles_revision_layer", "revision_id", "layer"),
        {"schema": "grid"},
    )

    revision_id = db.Column(UUID(as_uuid=True), nullable=False)
    layer = db.Column(Text, nullable=False)
    z = db.Column(Integer, nullable=False)
    x = db.Column(Integer, nullable=False)
    y = db.Column(Integer, nullable=False)
    payload = db.Column(LargeBinary, nullable=True)
    metadata_json = db.Column("metadata", JSONB, nullable=True)
