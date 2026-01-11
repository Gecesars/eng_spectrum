from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.extensions import db
from app.models import EmailToken, User


_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_email_token(user: User, purpose: str, ttl_hours: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)

    email_token = EmailToken(
        user_id=user.id,
        purpose=purpose,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.session.add(email_token)
    db.session.commit()
    return token


def consume_email_token(token: str, purpose: str) -> User | None:
    token_hash = _hash_token(token)
    now = datetime.now(timezone.utc)
    email_token = (
        EmailToken.query.filter_by(token_hash=token_hash, purpose=purpose)
        .filter(EmailToken.expires_at > now)
        .filter(EmailToken.used_at.is_(None))
        .first()
    )
    if not email_token:
        return None

    email_token.used_at = now
    db.session.commit()
    return email_token.user
