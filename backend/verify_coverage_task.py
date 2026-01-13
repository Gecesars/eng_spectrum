import sys
import os
sys.path.append(os.getcwd())

from app import create_app, db
from app.models.v4 import Job, V4Station, Network
from app.tasks.computation import calculate_coverage
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
import uuid

def test_coverage():
    app = create_app()
    with app.app_context():
        print("Creating test data...")
        # Create user if needed (omitted for speed, assuming existing FK or nullable)
        # Actually V4Station needs network_id.
        
        # Cleanup
        Network.query.filter_by(name="TestCovNet").delete()
        db.session.commit()
        
        net = Network(name="TestCovNet", owner_id=1) # Assuming user 1 exists (from clean install)
        # If user 1 doesn't exist, we might fail. Let's list users? 
        # Or just try.
        try:
             db.session.add(net)
             db.session.flush()
        except:
             db.session.rollback()
             # Maybe user 1 doesn't exist. create one?
             from backend.app.models import User
             u = User.query.first()
             if not u:
                 u = User(username="test", email="test@test.com")
                 u.set_password("test")
                 db.session.add(u)
                 db.session.flush()
             net = Network(name="TestCovNet", owner_id=u.id)
             db.session.add(net)
             db.session.flush()

        # Station
        st = V4Station(
            name="TestCovStation",
            network_id=net.id,
            geom=from_shape(Point(-47.0, -23.0)), # Lat/Lon
            htx=50.0,
            freq_mhz=100.0,
            erp_dbm=60.0 # 1kW
        )
        db.session.add(st)
        db.session.flush()
        
        # Job
        job = Job(user_id=net.owner_id, type="coverage", params={})
        db.session.add(job)
        db.session.commit()
        
        print(f"Running coverage task for Job {job.id}, Station {st.id}...")
        try:
            # Call calling directly
            result = calculate_coverage(None, job.id, st.id, radius_km=10.0, step_km=2.0)
            
            print("Task finished.")
            print(f"Center: {result.get('center')}")
            print(f"Points count: {len(result.get('points', []))}")
            if result.get('points'):
                print(f"Sample point: {result['points'][0]}")
                
            # Verify Job status
            db.session.refresh(job)
            print(f"Job Status: {job.status}")
            
        except Exception as e:
            print(f"Task Failed: {e}")
            import traceback
            traceback.print_exc()
            
        # Cleanup
        db.session.delete(job)
        db.session.delete(st)
        db.session.delete(net)
        db.session.commit()

if __name__ == "__main__":
    test_coverage()
