import sys
import os
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from backend.app import create_app, db

def test_mvt():
    app = create_app()
    with app.test_client() as client:
        # Request a tile that likely contains the "TestCovStation" (Lat -23, Lon -47)
        # Z=10, X=366, Y=564 covers Brazil roughly or use a converter.
        # For simple test, Z=0, X=0, Y=0 covers whole world
        response = client.get('/api/v4/tiles/ibge/0/0/0.pbf')
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Length: {len(response.data)} bytes")
        
        if response.status_code == 200 and len(response.data) > 0:
            print("SUCCESS: MVT endpoint returned data.")
        else:
            print("FAILED: No data or error.")

if __name__ == "__main__":
    test_mvt()
