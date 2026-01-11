
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.v4 import Network, V4Station, Job
from app.tasks.computation import calculate_link_profile
from sqlalchemy import func
import json

v4_bp = Blueprint('v4', __name__, url_prefix='/api/v4')

# --- NETWORKS ---

@v4_bp.route('/networks', methods=['GET'])
def list_networks():
    networks = Network.query.all()
    return jsonify([{
        'id': str(n.id),
        'name': n.name,
        'description': n.description,
        'created_at': n.created_at.isoformat() if n.created_at else None
    } for n in networks])

@v4_bp.route('/networks', methods=['POST'])
def create_network():
    data = request.json
    # Assume authenticated user for MVP (replace with current_user)
    # user_id = current_user.id
    from app.models import User
    user = User.query.first() # Placeholder
    
    if not user:
        return jsonify({'error': 'No user available'}), 400
        
    network = Network(
        name=data.get('name', 'New Network'),
        description=data.get('description', ''),
        owner_user_id=user.id
    )
    db.session.add(network)
    db.session.commit()
    return jsonify({'id': str(network.id), 'name': network.name}), 201

# --- STATIONS ---

@v4_bp.route('/networks/<network_id>/stations', methods=['GET'])
def list_stations(network_id):
    """Returns stations as GeoJSON FeatureCollection"""
    stations = V4Station.query.filter_by(network_id=network_id).all()
    
    features = []
    for s in stations:
        # Check geom
        # We can use db.session.scalar(func.ST_AsGeoJSON(s.geom)) but simplest is if we manually construct it
        # or rely on s.geom being returned as WKBElement or similar.
        # Let's simple query manual conversion for now or assume s.geom has simple accessors if using GeoAlchemy2 correctly.
        # s.geom is WKBElement.
        
        # Helper to get geom
        try:
            geom_json = db.session.scalar(func.ST_AsGeoJSON(s.geom))
            geom = json.loads(geom_json)
        except:
            geom = None

        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "id": str(s.id),
                "name": s.entidade,
                "service": s.service,
                "freq": s.freq_mhz,
                "erp": s.erp_dbm
            }
        })
        
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })

@v4_bp.route('/stations', methods=['POST'])
def create_station():
    data = request.json
    network_id = data.get('network_id')
    
    lat = data.get('lat')
    lon = data.get('lon')
    
    wkt = f"POINT({lon} {lat})"
    
    station = V4Station(
        network_id=network_id,
        entidade=data.get('name', 'New Station'),
        geom=func.ST_GeomFromText(wkt, 4674),
        freq_mhz=data.get('freq_mhz'),
        erp_dbm=data.get('erp_dbm'),
        htx=data.get('htx', 30.0)
    )
    db.session.add(station)
    db.session.commit()
    return jsonify({'id': str(station.id)}), 201

# --- JOBS (CALCULATIONS) ---

@v4_bp.route('/jobs/link', methods=['POST'])
def create_link_job():
    data = request.json
    tx_id = data.get('tx_id')
    rx_id = data.get('rx_id') # If RX is a station
    # rx_point = data.get('rx_point') # If arbitrary point? Not implemented yet.
    
    # Create Job
    job = Job(
        network_id=data.get('network_id'), # Optional
        type='link_profile',
        status='pending',
        params=data
    )
    db.session.add(job)
    db.session.commit()
    
    # Trigger Celery
    task = calculate_link_profile.delay(job.id, tx_id, rx_id)
    
    return jsonify({'job_id': str(job.id), 'task_id': task.id}), 202

@v4_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    job = Job.query.get_or_404(job_id)
    return jsonify({
        'id': str(job.id),
        'status': job.status,
        'progress': job.progress,
        'result': job.result_ref,
        'error': job.error
    })
