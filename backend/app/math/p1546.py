
import numpy as np
from numba import njit, float64, int32

# Monkey patch np.mat for Py1546 (uses deprecated API)
if not hasattr(np, 'mat'):
    np.mat = np.asmatrix

try:
    from Py1546.P1546 import bt_loss
except ImportError:
    bt_loss = None

@njit(cache=True, fastmath=True)
def bilinear_sample(dem, r, c):
    h, w = dem.shape
    r0 = int(r)
    c0 = int(c)
    if r0 < 0 or r0 >= h - 1 or c0 < 0 or c0 >= w - 1:
        return 0.0 # Out of bounds
        
    delta_r = r - r0
    delta_c = c - c0
    
    val00 = dem[r0, c0]
    val01 = dem[r0, c0+1]
    val10 = dem[r0+1, c0]
    val11 = dem[r0+1, c0+1]
    
    top = val00 * (1 - delta_c) + val01 * delta_c
    bot = val10 * (1 - delta_c) + val11 * delta_c
    
    return top * (1 - delta_r) + bot * delta_r

@njit(cache=True, fastmath=True)
def get_terrain_avg_3_15(dem, dem_ul_x, dem_ul_y, cell_size_x, cell_size_y, tx_x, tx_y, azimuth_deg):
    """
    Calculates average terrain height between 3km and 15km from TX along azimuth.
    Assumes projected coordinates (meters).
    """
    rad = np.radians(azimuth_deg)
    sin_a = np.sin(rad)
    cos_a = np.cos(rad)
    
    dist_start = 3000.0
    dist_end = 15000.0
    step = 100.0 # 100m step
    
    sum_h = 0.0
    count = 0
    
    d = dist_start
    while d <= dist_end:
        # Target point relative to TX
        dx = d * sin_a
        dy = d * cos_a
        
        # Target absolute
        px = tx_x + dx
        py = tx_y + dy
        
        # Map to raster indices
        # Assumes standard transform: x = ul_x + c*cell_x, y = ul_y + r*cell_y
        c = (px - dem_ul_x) / cell_size_x
        r = (py - dem_ul_y) / cell_size_y 
        
        h_val = bilinear_sample(dem, r, c)
        sum_h += h_val
        count += 1
        d += step
        
    if count == 0:
        return 0.0
        
    return sum_h / count

def calc_p1546_point(freq_mhz, time_pct, tx_h_eff, rx_h, distance_km, env_type='Rural', 
                    path_type='Land', location_pct=50, tx_erp_kw=1.0):
    """
    Wrapper for Py1546.bt_loss.
    Returns (Field Strength dBuV/m, Loss dB)
    """
    if bt_loss is None:
        raise ImportError("Py1546 not installed")

    # Map inputs to Py1546 expectations
    f = float(freq_mhz)
    t = float(time_pct)
    heff = float(tx_h_eff)
    h2 = float(rx_h)
    
    # R2 clutter height defaults
    R2 = 10.0
    if env_type == 'Urban':
        R2 = 20.0
    elif env_type == 'Dense Urban':
        R2 = 30.0
        
    area = env_type
    d_v = np.array([float(distance_km)])
    path_c = np.array([path_type]) # 'Land', 'Sea', 'Warm', 'Cold'
    pathinfo = 0 # No detailed profile info for now
    
    # *args unpacking: q, wa, PTx, ha, hb, R1, tca, htter, hrter, eff1, eff2, debug, fid_log
    q = float(location_pct) # Location variability
    wa = 50.0 # Default width
    PTx = float(tx_erp_kw)
    ha = 0.0 # Not used if not Annex 5 sec 3.1.1? Doc says "> 1 m". Let's pass heff or similar if needed. 
             # Actually bt_loss doc says: "Transmitter antenna height above ground."
             # If we don't have it (we have heff), effectively it might be used for corrections.
             # We should try to pass a reasonable value if known, or heff. 
             # But heff is height over avg terrain. ha is height above ground at TX.
    ha = heff # Fallback if unknown, or we should ask caller to provide it.
    
    hb = 0.0 
    R1 = 10.0 # TX clutter
    tca = 0.0
    htter = 0.0
    hrter = 0.0
    eff1 = 0.0
    eff2 = 0.0
    debug = 0
    fid_log = 0 
    
    # Call bt_loss
    # Note: args must be passed positionally after pathinfo
    Es, L = bt_loss(f, t, heff, h2, R2, area, d_v, path_c, pathinfo,
                    q, wa, PTx, ha, hb, R1, tca, htter, hrter, eff1, eff2, debug, fid_log)
                    
    return Es, L
