import sys
import os
sys.path.append(os.getcwd())

from backend.app.math.p1546 import calc_p1546_point

def test_p1546():
    print("Testing P.1546 Calculation...")
    try:
        # 100 MHz, 50% time, Tx 30m, Rx 10m, 10km distance, Land
        es, loss = calc_p1546_point(100.0, 50.0, 30.0, 10.0, 10.0, env_type='Rural')
        print(f"Result: Field Strength = {es} dBuV/m, Loss = {loss} dB")
        
        if es > 0:
            print("SUCCESS: Calculation returned positive field strength.")
        else:
            print("WARNING: Field strength is <= 0.")
            
    except ImportError as e:
        print(f"FAILED: {e}")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_p1546()
