from __future__ import annotations

import os

from flask import Blueprint, send_from_directory


frontend_bp = Blueprint("frontend", __name__)


def _frontend_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend"))


@frontend_bp.route("/")
def index():
    return send_from_directory(_frontend_root(), "index.html")


@frontend_bp.route("/styles.css")
def styles():
    return send_from_directory(_frontend_root(), "styles.css")


@frontend_bp.route("/app.js")
def app_js():
    return send_from_directory(_frontend_root(), "app.js")
