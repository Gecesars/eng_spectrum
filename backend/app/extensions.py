from __future__ import annotations

from celery import Celery
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()
celery_app = Celery(__name__)
