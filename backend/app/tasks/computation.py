
import json
from app.extensions import celery_app, db
from app.models.v4 import Job, V4Station, Network
from app.math.deygout import calc_deygout_loss
import numpy as np

# Mock implementation of profile extraction for now
# In production this would read from indexed rasters
def extract_profile_from_rasters(tx_geom, rx_geom, resolution_m=30):
    # Retrieve coordinates
    # For MVP we return a dummy flat earth profile with some obstacles
    lat1, lon1 = tx_geom.y, tx_geom.x
    lat2, rx_lon = rx_geom.y, rx_geom.x
    
    # Calculate distance (Vincenty or Haversine)
    # Simplified haversine for MVP
    R = 6371000
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(rx_lon - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    dist_total = R * c
    
    n_points = int(dist_total / resolution_m)
    dist_m = np.linspace(0, dist_total, n_points)
    
    # Dummy elevation: 100m flat + a hill in the middle
    elev_m = np.full(n_points, 100.0)
    
    # Add a hill at 50% distance
    mid = n_points // 2
    width = n_points // 10
    hill = np.exp(-0.5 * ((np.arange(n_points) - mid) / width)**2) * 200 # 200m hill
    elev_m += hill
    
    return dist_m, elev_m

@celery_app.task(bind=True)
def calculate_link_profile(self, job_id, tx_id, rx_id):
    """
    Calculates link profile and diffraction loss between two stations.
    """
    job = Job.query.get(job_id)
    if not job:
        return {"error": "Job not found"}
        
    job.status = "running"
    db.session.commit()
    
    try:
        tx = V4Station.query.get(tx_id)
        # rx could be a station or just a point. Assuming station for now or we create a temporary object.
        # For this test we assume rx_id is a station too.
        rx = V4Station.query.get(rx_id)
        
        if not tx or not rx:
            raise ValueError("Stations not found")
            
        # Extract profile
        dist_m, elev_m = extract_profile_from_rasters(tx.geom, rx.geom)
        
        # Calculate loss
        freq_mhz = tx.freq_mhz or 100.0
        tx_h = tx.htx or 30.0
        rx_h = rx.htx or 10.0
        
        loss_db = calc_deygout_loss(dist_m, elev_m, freq_mhz, tx_h, rx_h)
        
        # Prepare result
        result = {
            "loss_db": float(loss_db),
            "distance_km": dist_m[-1] / 1000.0,
            "profile_sample_count": len(dist_m)
        }
        
        job.result_ref = result
        job.status = "done"
        job.progress = 100
        db.session.commit()
        
        return result
        
    except Exception as e:
        job.status = "error"
        job.error = str(e)
        db.session.commit()
        raise e
