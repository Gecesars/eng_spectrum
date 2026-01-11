from __future__ import annotations

from flask import Blueprint, jsonify, request, g

from app.extensions import db
from app.models import Project
from app.utils.auth import require_auth


projects_bp = Blueprint("projects", __name__, url_prefix="/api/projects")


@projects_bp.get("")
@require_auth
def list_projects():
    projects = Project.query.filter_by(user_id=g.current_user.id).order_by(Project.created_at.desc()).all()
    return jsonify(
        [
            {
                "id": str(p.id),
                "name": p.name,
                "service_type": p.service_type,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "current_revision_id": str(p.current_revision_id) if p.current_revision_id else None,
            }
            for p in projects
        ]
    )


@projects_bp.post("")
@require_auth
def create_project():
    payload = request.get_json(force=True)
    name = payload.get("name", "").strip()
    service_type = payload.get("service_type", "").strip()
    if not name or not service_type:
        return jsonify({"error": "name_and_service_required"}), 400

    project = Project(
        user_id=g.current_user.id,
        name=name,
        service_type=service_type,
        status="draft",
    )
    db.session.add(project)
    db.session.commit()

    return (
        jsonify(
            {
                "id": str(project.id),
                "name": project.name,
                "service_type": project.service_type,
                "status": project.status,
            }
        ),
        201,
    )


@projects_bp.get("/<project_id>")
@require_auth
def get_project(project_id: str):
    project = Project.query.filter_by(id=project_id, user_id=g.current_user.id).first()
    if not project:
        return jsonify({"error": "not_found"}), 404

    return jsonify(
        {
            "id": str(project.id),
            "name": project.name,
            "service_type": project.service_type,
            "status": project.status,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "current_revision_id": str(project.current_revision_id) if project.current_revision_id else None,
        }
    )
