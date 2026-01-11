from __future__ import annotations

import os


def _get_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://engapp:engapp@localhost:5432/engenharia_espectro",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    CELERY_TASK_ALWAYS_EAGER = _get_bool(os.getenv("CELERY_TASK_ALWAYS_EAGER"), default=True)

    SRID = int(os.getenv("SRID", "4674"))
    EXPORT_DIR = os.getenv("EXPORT_DIR", "/home/atx/eng_spectrum/exports")
    FILE_STORAGE_DIR = os.getenv("FILE_STORAGE_DIR", "/home/atx/eng_spectrum/storage")

    EMAIL_TOKEN_TTL_HOURS = int(os.getenv("EMAIL_TOKEN_TTL_HOURS", "24"))
    PASSWORD_RESET_TTL_HOURS = int(os.getenv("PASSWORD_RESET_TTL_HOURS", "2"))

    SMTP_HOST = os.getenv("SMTP_HOST") or os.getenv("MAIL_SERVER", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT") or os.getenv("MAIL_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER") or os.getenv("MAIL_USERNAME", "")
    SMTP_PASS = os.getenv("SMTP_PASS") or os.getenv("MAIL_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM") or os.getenv("MAIL_DEFAULT_SENDER", "no-reply@engspec.local")
    SMTP_USE_TLS = _get_bool(os.getenv("SMTP_USE_TLS") or os.getenv("MAIL_USE_TLS"), default=True)
    SMTP_USE_SSL = _get_bool(os.getenv("SMTP_USE_SSL") or os.getenv("MAIL_USE_SSL"), default=False)

    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
    ANATEL_DATA_DIR = os.getenv("ANATEL_DATA_DIR", "/home/atx/eng_spectrum/anatel")
