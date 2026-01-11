
import os
import re
import glob
from app import create_app
from app.extensions import db
from app.models.v4 import Raster
from sqlalchemy import func

# SRTM HGT convention:
# NxxEyyy.hgt or SxxWyyy.hgt
# Coordinates refer to lower-left corner of the tile.
# 1-arc-second (SRTM1) = 3601x3601 samples
# 3-arc-second (SRTM3) = 1201x1201 samples

DEM_DIR = os.path.join(os.getcwd(), 'anatel', 'DEM')

def parse_hgt_filename(filename):
    """
    Parses HGT filename (e.g. S23W045.hgt) and returns (lat, lon).
    Returns None if pattern doesn't match.
    """
    basename = os.path.basename(filename)
    name, ext = os.path.splitext(basename)
    if ext.lower() != '.hgt':
        return None
        
    pattern = r"([Ns])(\d+)([EeWw])(\d+)"
    match = re.match(pattern, name)
    if not match:
        return None
        
    ns, lat_str, ew, lon_str = match.groups()
    lat = int(lat_str)
    lon = int(lon_str)
    
    if ns.upper() == 'S':
        lat = -lat
    if ew.upper() == 'W':
        lon = -lon
        
    return lat, lon

def estimate_resolution(filepath):
    """
    Estimates resolution in arc-seconds based on file size.
    """
    size = os.path.getsize(filepath)
    # 1201*1201*2 = 2884802 bytes -> 3 arcsec
    # 3601*3601*2 = 25934402 bytes -> 1 arcsec
    
    if 2800000 < size < 2900000:
        return 3.0
    elif 25000000 < size < 26000000:
        return 1.0
    else:
        # Default fallback or error
        return 3.0 

def index_tiles():
    app = create_app()
    with app.app_context():
        print(f"Scanning {DEM_DIR}...")
        files = glob.glob(os.path.join(DEM_DIR, "*.hgt"))
        
        count_new = 0
        count_updated = 0
        
        for filepath in files:
            res = parse_hgt_filename(filepath)
            if not res:
                # print(f"Skipping invalid file: {filepath}")
                continue
            
            lat_min, lon_min = res
            resolution = estimate_resolution(filepath)
            
            # Construct bbox (POLYGON)
            # Tile covers 1x1 degree
            lat_max = lat_min + 1
            lon_max = lon_min + 1
            
            # WKT Polygon: (lon_min lat_min, lon_max lat_min, lon_max lat_max, lon_min lat_max, lon_min lat_min)
            wkt = f"POLYGON(({lon_min} {lat_min}, {lon_max} {lat_min}, {lon_max} {lat_max}, {lon_min} {lat_max}, {lon_min} {lat_min}))"
            
            filename = os.path.basename(filepath)
            
            # Check if exists
            raster = Raster.query.filter_by(filename=filename).first()
            if not raster:
                raster = Raster(
                    filename=filename,
                    resolution_arcsec=resolution,
                    bbox=func.ST_GeomFromText(wkt, 4674)
                )
                db.session.add(raster)
                count_new += 1
            else:
                # Verify/Update if needed?
                # For now just skip
                pass
        
        db.session.commit()
        print(f"Indexing complete. New: {count_new}, Total files: {len(files)}")

if __name__ == "__main__":
    index_tiles()
