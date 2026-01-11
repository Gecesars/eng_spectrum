
import numpy as np
import time
from app.math.deygout import calc_deygout_loss

def verify_deygout():
    print("Verifying Deygout...")
    dist_m = np.linspace(0, 50000, 1000) # 50km
    elev_m = np.full(1000, 100.0) # Flat terrain at 100m
    
    # Add obstacle
    mid = 500
    elev_m[mid] += 200 # 300m total height at mid path
    
    freq = 100.0 # MHz
    tx_h = 30.0
    rx_h = 10.0
    
    start = time.time()
    loss = calc_deygout_loss(dist_m, elev_m, freq, tx_h, rx_h)
    end = time.time()
    
    print(f"Loss: {loss:.2f} dB")
    print(f"Time: {(end-start)*1000:.2f} ms")
    
    if loss > 0:
        print("PASS: Loss calculated.")
    else:
        print("FAIL: Loss is 0 (should be >0 for blocked path).")

if __name__ == "__main__":
    verify_deygout()
