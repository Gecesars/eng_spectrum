from __future__ import annotations

import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from app.config import Config
from app.extensions import celery_app, db, migrate


def _ensure_dirs(app: Flask) -> None:
    os.makedirs(app.config["EXPORT_DIR"], exist_ok=True)
    os.makedirs(app.config["FILE_STORAGE_DIR"], exist_ok=True)


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    _ensure_dirs(app)

    from app.routes.auth import auth_bp
    from app.routes.frontend import frontend_bp
    from app.routes.projects import projects_bp
    from app.routes.revisions import revisions_bp
    from app.routes.station import station_bp
    from app.routes.results import results_bp
    from app.routes.export import export_bp
    from app.cli import engspec_cli
    from app.routes.anatel import anatel_bp
    from app.routes.v4 import v4_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(revisions_bp)
    app.register_blueprint(station_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(frontend_bp)
    app.register_blueprint(anatel_bp)
    app.register_blueprint(v4_bp)
    app.cli.add_command(engspec_cli)

    init_celery(app)

    return app


def init_celery(app: Flask) -> None:
    celery_app.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_always_eager=app.config["CELERY_TASK_ALWAYS_EAGER"],
    )

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
