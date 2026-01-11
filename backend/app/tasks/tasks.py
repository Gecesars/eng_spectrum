from __future__ import annotations

from app.extensions import celery_app
from app.models import Contour, ProjectRevision
from app.services.contour import compute_contour
from app.services.export import export_kml, export_mosaico_txt, export_shapefile
from app.services.interference import run_interference_case
from app.services.opea import run_opea_assessment
from app.services.rni import run_rni_assessment


@celery_app.task
def run_contour(revision_id: str, threshold_dbuvm: float, step_deg: int = 5, step_km: float = 0.1):
    revision = ProjectRevision.query.get(revision_id)
    if not revision:
        raise ValueError("Revision not found")
    result = compute_contour(revision, threshold_dbuvm, step_deg=step_deg, step_km=step_km)
    return {"contour_id": str(result.contour.id)}


@celery_app.task
def run_interference(revision_id: str):
    revision = ProjectRevision.query.get(revision_id)
    if not revision:
        raise ValueError("Revision not found")
    results = []
    for case in revision.interference_cases:
        result = run_interference_case(revision, case)
        results.append({"case_id": str(result.case.id), "passed": result.passed})
    return results


@celery_app.task
def run_rni(revision_id: str, s_limit_public: float, s_limit_occ: float, k_reflection: float = 2.56):
    revision = ProjectRevision.query.get(revision_id)
    if not revision:
        raise ValueError("Revision not found")
    result = run_rni_assessment(
        revision,
        s_limit_w_m2_public=s_limit_public,
        s_limit_w_m2_occ=s_limit_occ,
        k_reflection=k_reflection,
    )
    return {"rni_id": str(result.assessment.id), "r_public_m": result.assessment.r_public_m, "r_occ_m": result.assessment.r_occ_m}


@celery_app.task
def run_opea(revision_id: str, aerodrome_ref: str | None = None, aerodrome_lat: float | None = None, aerodrome_lon: float | None = None):
    revision = ProjectRevision.query.get(revision_id)
    if not revision:
        raise ValueError("Revision not found")
    result = run_opea_assessment(revision, aerodrome_ref, aerodrome_lat, aerodrome_lon)
    return {"opea_id": str(result.assessment.id), "result": result.assessment.result}


@celery_app.task
def export_revision_kml(contour_id: str, export_dir: str):
    contour = Contour.query.get(contour_id)
    if not contour:
        raise ValueError("Contour not found")
    return export_kml(contour, export_dir)


@celery_app.task
def export_revision_mosaico(contour_id: str, export_dir: str):
    contour = Contour.query.get(contour_id)
    if not contour:
        raise ValueError("Contour not found")
    return export_mosaico_txt(contour, export_dir)


@celery_app.task
def export_revision_shp(contour_id: str, export_dir: str):
    contour = Contour.query.get(contour_id)
    if not contour:
        raise ValueError("Contour not found")
    return export_shapefile(contour, export_dir)
