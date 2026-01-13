
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

@celery_app.task(bind=True)
def calculate_coverage(self, job_id, tx_id, radius_km=50.0, step_km=1.0):
    """
    Calculates P.1546 coverage (omnidirectional).
    Returns a list of points (lat, lon, dBuV/m).
    """
    job = Job.query.get(job_id)
    if not job:
        return {"error": "Job not found"}
    
    job.status = "running"
    db.session.commit()

    try:
        tx = V4Station.query.get(tx_id)
        if not tx:
            raise ValueError("Station not found")

        # Basic parameters
        freq = tx.freq_mhz or 100.0
        erp = (tx.erp_dbm or 60.0) / 10.0 # dBm -> dBW? No, Py1546 expects kW usually? 
        # wrapper takes tx_erp_kw. 
        # erp_dbm -> mW -> W -> kW
        # 60 dBm = 1000 W = 1 kW.
        # 10^(dbm/10) = mW. 
        erp_mw = 10**( (tx.erp_dbm or 60.0) / 10.0 )
        erp_kw = erp_mw / 1_000_000.0
        
        tx_h_agl = tx.htx or 30.0
        # tx_ground = ... need DEM ...
        # For MVP we assume flat earth or fetch from DEM if possible.
        # We need a proper way to get DEM.
        # For now, let's use a placeholder for terrain height fetching.
        
        # We'll compute 36 radials (every 10 deg)
        points = []
        
        lat0 = tx.geom.y
        lon0 = tx.geom.x
        
        # We need projected coordinates for distance/azimuth usually, but for low precision we use spherical.
        # Py1546 needs heff. 
        # heff = h_agl + h_ground - avg_terrain(3-15km).
        # We'll assume heff = h_agl for now to avoid complexity of DEM fetching in this task file without raster access.
        # TODO: Inject RasterService or similar.
        
        heff = tx_h_agl # Simplification
        
        from app.math.p1546 import calc_p1546_point
         
        for az in range(0, 360, 10):
            # Compute points along radial
            for dist in range(1, int(radius_km)+1, int(step_km or 1)):
                 # Calculate lat/lon of point
                 # Simple flat earth approximation for small distances
                 # lat = lat0 + (dist/111) * cos(az)
                 # lon = lon0 + (dist/(111*cos(lat))) * sin(az)
                 
                 rad = np.radians(az)
                 d_deg = dist / 111.0 # Rough degrees
                 
                 p_lat = lat0 + d_deg * np.cos(rad)
                 p_lon = lon0 + d_deg * np.sin(rad) / np.cos(np.radians(lat0))
                 
                 es, loss = calc_p1546_point(
                     freq_mhz=freq,
                     time_pct=50,
                     tx_h_eff=heff,
                     rx_h=10.0, # Standard mobile height
                     distance_km=float(dist),
                     env_type='Rural', # Default
                     tx_erp_kw=erp_kw
                 )
                 
                 points.append({
                     "lat": p_lat,
                     "lon": p_lon,
                     "val": round(es, 1),
                     "dist": dist,
                     "az": az
                 })
                 
        result = {
            "points": points,
            "center": {"lat": lat0, "lon": lon0},
            "radius": radius_km
        }
        
        job.result_ref = result # This might be large, but ok for MVP (few KB).
        job.status = "done"
        job.progress = 100
        db.session.commit()
        
        return result

    except Exception as e:
        job.status = "error"
        job.error = str(e)
        db.session.commit()
        raise e

