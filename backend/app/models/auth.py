from __future__ import annotations

import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(Text, unique=True, nullable=False)
    email_verified = db.Column(Boolean, default=False)
    password_hash = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = db.Column(DateTime(timezone=True), nullable=True)


class EmailToken(db.Model):
    __tablename__ = "email_tokens"
    __table_args__ = {"schema": "auth"}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    purpose = db.Column(Text, nullable=False)
    token_hash = db.Column(Text, nullable=False)
    expires_at = db.Column(DateTime(timezone=True), nullable=False)
    used_at = db.Column(DateTime(timezone=True), nullable=True)

    user = db.relationship("User", backref="email_tokens")
