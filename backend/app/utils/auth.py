from __future__ import annotations

from functools import wraps

from flask import g, jsonify, request

from app.services.session import verify_token


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "missing_token"}), 401
        user = verify_token(parts[1])
        if not user:
            return jsonify({"error": "invalid_token"}), 401
        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper
