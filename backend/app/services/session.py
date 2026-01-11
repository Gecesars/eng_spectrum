from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from flask import current_app

from app.models import User


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["JWT_SECRET"], salt="eng-spec-auth")


def generate_token(user: User) -> str:
    return _serializer().dumps({"user_id": str(user.id)})


def verify_token(token: str, max_age_seconds: int = 60 * 60 * 12) -> User | None:
    try:
        payload = _serializer().loads(token, max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
    return User.query.get(payload.get("user_id"))
