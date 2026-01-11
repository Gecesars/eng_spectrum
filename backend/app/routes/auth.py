from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.models import User
from app.services.auth import create_email_token, hash_password, consume_email_token, verify_password
from app.services.email import build_confirm_email, build_reset_email, send_email
from app.services.session import generate_token


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    payload = request.get_json(force=True)
    email = payload.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "email_required"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing and existing.email_verified:
        return jsonify({"error": "email_in_use"}), 409

    if not existing:
        user = User(email=email, email_verified=False)
        db.session.add(user)
        db.session.commit()
    else:
        user = existing

    token = create_email_token(user, "confirm_email", current_app.config["EMAIL_TOKEN_TTL_HOURS"])
    subject, body = build_confirm_email(token)
    try:
        send_email(user.email, subject, body)
    except RuntimeError:
        return jsonify({"error": "smtp_not_configured"}), 500
    except Exception:
        return jsonify({"error": "smtp_send_failed"}), 502

    return jsonify({"message": "confirmation_sent"}), 201


@auth_bp.post("/confirm")
def confirm_email():
    payload = request.get_json(force=True)
    token = payload.get("token", "")
    password = payload.get("password", "")
    if not token or not password:
        return jsonify({"error": "token_and_password_required"}), 400
    if len(password) < 6:
        return jsonify({"error": "password_too_short"}), 400

    user = consume_email_token(token, "confirm_email")
    if not user:
        return jsonify({"error": "invalid_or_expired_token"}), 400

    if user.email_verified and user.password_hash:
        return jsonify({"message": "already_confirmed"}), 200

    user.password_hash = hash_password(password)
    user.email_verified = True
    db.session.commit()

    return jsonify({"message": "email_confirmed"}), 200


@auth_bp.post("/login")
def login():
    payload = request.get_json(force=True)
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")
    if not email or not password:
        return jsonify({"error": "email_and_password_required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.password_hash:
        return jsonify({"error": "invalid_credentials"}), 401
    if not user.email_verified:
        return jsonify({"error": "email_not_verified"}), 403

    if not verify_password(password, user.password_hash):
        return jsonify({"error": "invalid_credentials"}), 401

    token = generate_token(user)
    user.last_login_at = db.func.now()
    db.session.commit()

    return jsonify({"token": token}), 200


@auth_bp.post("/forgot")
def forgot_password():
    payload = request.get_json(force=True)
    email = payload.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "email_required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "ok"}), 200

    token = create_email_token(user, "reset_password", current_app.config["PASSWORD_RESET_TTL_HOURS"])
    subject, body = build_reset_email(token)
    try:
        send_email(user.email, subject, body)
    except RuntimeError:
        return jsonify({"error": "smtp_not_configured"}), 500
    except Exception:
        return jsonify({"error": "smtp_send_failed"}), 502
    return jsonify({"message": "reset_sent"}), 200


@auth_bp.post("/reset")
def reset_password():
    payload = request.get_json(force=True)
    token = payload.get("token", "")
    password = payload.get("new_password", "")
    if not token or not password:
        return jsonify({"error": "token_and_password_required"}), 400
    if len(password) < 6:
        return jsonify({"error": "password_too_short"}), 400

    user = consume_email_token(token, "reset_password")
    if not user:
        return jsonify({"error": "invalid_or_expired_token"}), 400

    user.password_hash = hash_password(password)
    db.session.commit()

    return jsonify({"message": "password_reset"}), 200


@auth_bp.post("/logout")
def logout():
    return jsonify({"message": "ok"}), 200
