
import numpy as np
from numba import njit, float64, int32

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
        # Usually cell_y is negative for top-down images (north-up DEM)
        
        c = (px - dem_ul_x) / cell_size_x
        r = (py - dem_ul_y) / cell_size_y 
        
        h_val = bilinear_sample(dem, r, c)
        sum_h += h_val
        count += 1
        d += step
        
    if count == 0:
        return 0.0
        
    return sum_h / count
