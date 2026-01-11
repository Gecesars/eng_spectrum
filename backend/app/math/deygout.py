
import numpy as np
from numba import njit
import math

# Constants
EARTH_RADIUS = 6371000.0  # meters

@njit(cache=True, fastmath=True)
def calculate_fresnel_nu(h, d1, d2, lam):
    """
    Calculates Fresnel-Kirchhoff diffraction parameter (nu).
    h: obstacle height above LOS (meters)
    d1: distance from TX to obstacle (meters)
    d2: distance from obstacle to RX (meters)
    lam: wavelength (meters)
    """
    if d1 <= 0 or d2 <= 0:
        return 0.0
    val = (2.0 * (d1 + d2)) / (lam * d1 * d2)
    if val < 0:
        return 0.0
    return h * np.sqrt(val)

@njit(cache=True, fastmath=True)
def diffraction_loss_db(nu):
    """
    Lee approximation for knife-edge diffraction loss (dB).
    """
    if nu <= -0.7:
        return 0.0
    elif nu <= 0:
        return 6.0 + 9.0 * nu + 1.27 * (nu**2) # Approximate curve near grazing
    elif nu <= 1:
        return 6.9 + 13.0 * np.log10(nu - 0.1) # Lee's approx, requires nu > 0.1 usually. 
        # Better approx for nu > -0.7:
        # J(v) = 6.9 + 20 * log10(sqrt((v-0.1)^2 + 1) + v - 0.1)
    
    # Standard ITU-R P.526 approx for v > -0.7
    v = nu
    if v < -0.78:
        return 0.0
    elif v < 1.0: # Transition
        return 6.9 + 20 * np.log10(np.sqrt((v-0.1)**2 + 1) + v - 0.1)
    else:
        return 13 + 20 * np.log10(v)

@njit(cache=True, fastmath=True)
def deygout_recursive(dist_m, elev_m_w_earth, start_idx, end_idx, lam, h_tx_abs, h_rx_abs):
    """
    Recursive Deygout diffraction calculation.
    """
    if end_idx - start_idx < 2:
        return 0.0

    d_total = dist_m[end_idx] - dist_m[start_idx]
    if d_total <= 1e-3:
        return 0.0

    # Line of Sight (LOS) defined by (d_start, h_start) to (d_end, h_end)
    # y = mx + c relative to start point
    # h(x) = h_start + (h_end - h_start) * (x / d_total)
    
    # Endpoints heights (absolute AMSL)
    # For recursion, the 'TX' and 'RX' are the peaks of the previous step.
    # Initial call uses actual TX and RX antenna heights.
    
    # Note: On recursive calls, h_tx_abs and h_rx_abs are the obstacle heights (terrain) 
    # effectively acting as new terminals.
    
    h_start = h_tx_abs
    h_end = h_rx_abs
    d_start = dist_m[start_idx]
    
    max_nu = -9999.0
    max_idx = -1
    max_h_obs = 0.0 # Height of obstacle above LOS
    
    # Scan for max nu
    for i in range(start_idx + 1, end_idx):
        d_curr = dist_m[i]
        d_from_start = d_curr - d_start
        d_from_end = d_total - d_from_start
        
        # LOS height at this distance
        h_los = h_start + (h_end - h_start) * (d_from_start / d_total)
        
        h_terrain = elev_m_w_earth[i]
        h_obs = h_terrain - h_los # Height above LOS
        
        # We only care about obstructions or near-obstructions
        # Often we consider even negative h_obs (clearance check) but for strict Deygout main obstacle usually max nu.
        
        nu = calculate_fresnel_nu(h_obs, d_from_start, d_from_end, lam)
        
        if nu > max_nu:
            max_nu = nu
            max_idx = i
            max_h_obs = h_obs # Store if needed for Assis correction

    # If max_nu suggests significant diffraction (or we want full recursion)
    # Threshold usually around -0.78 or similar.
    if max_nu > -0.78:
        # Calculate loss for this obstacle
        loss_main = diffraction_loss_db(max_nu)
        
        # Recursion
        # Left sub-path: start to max_idx
        # effectively TX to ObstaclePeak
        # The new 'RX' height is the terrain height at obstacle.
        # Strict Deygout uses the obstacle peak.
        loss_left = deygout_recursive(dist_m, elev_m_w_earth, start_idx, max_idx, lam, h_start, elev_m_w_earth[max_idx])
        
        # Right sub-path: max_idx to end
        loss_right = deygout_recursive(dist_m, elev_m_w_earth, max_idx, end_idx, lam, elev_m_w_earth[max_idx], h_end)
        
        # Total loss (approximation rule, sometimes T-correction or similar applies)
        # Power sum or arithmetic sum depending on method variant. Deygout adds them.
        return loss_main + loss_left + loss_right
    else:
        return 0.0

@njit(cache=True, fastmath=True)
def get_earth_curvature_bias(d, k_factor, R_e=EARTH_RADIUS):
    # h = d^2 / (2 * k * Re) approx parabolic
    # Usually we apply this to the terrain: h_terrain_apparent = h_terrain_real - h_bias?
    # Or h_bias = (d1 * d2) / (2 * k * Re) for bulge.
    # Here we probably pre-curve the terrain or use a flat earth model with curved rays.
    # Flat earth with curved rays: Ray curvature 1/(k*Re).
    # Equivalent to Earth with effective radius k*Re and straight rays.
    # Standard approach: Transform terrain heights relative to straight line chord?
    # Or just add earth bulge to terrain heights (if plotting relative to flat line).
    pass

@njit(cache=True, fastmath=True)
def calc_deygout_loss(dist_m, elev_m, freq_mhz, tx_h_agl, rx_h_agl, k_factor=1.333):
    """
    Main entry point for Deygout Loss.
    dist_m: array of distances from TX (0..D)
    elev_m: array of terrain altitudes (AMSL)
    """
    lam = 300.0 / freq_mhz # wavelength in meters
    R_eff = k_factor * EARTH_RADIUS
    
    n_points = len(dist_m)
    if n_points < 2:
        return 0.0
        
    D_total = dist_m[-1]
    
    # 1. Apply Earth Curvature (Bulge) to terrain
    # We treat the line connecting TX (ground) and RX (ground) as flat, 
    # and bulge the earth up.
    # bulge(d) = d * (D - d) / (2 * R_eff)
    
    elev_curved = np.empty(n_points, dtype=np.float64)
    for i in range(n_points):
        d = dist_m[i]
        bulge = (d * (D_total - d)) / (2.0 * R_eff)
        # Actually standard practice for 'profile over flat earth': 
        # y_terrain = h_ground + bulge
        elev_curved[i] = elev_m[i] + bulge

    # TX and RX absolute heights
    h_tx_abs = elev_curved[0] + tx_h_agl
    h_rx_abs = elev_curved[-1] + rx_h_agl
    
    # Recursive calculation
    loss = deygout_recursive(dist_m, elev_curved, 0, n_points - 1, lam, h_tx_abs, h_rx_abs)
    
    # Clutter loss could be added here
    return loss
