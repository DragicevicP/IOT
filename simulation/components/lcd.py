import time
from settings import is_simulated

def _ts():
    return time.strftime("%H:%M:%S")

def run_lcd(device_settings, registry: dict, stop_event):
    simulated = is_simulated(device_settings)

    if simulated:
        from simulators.lcd import SimLCD
        lcd = SimLCD(cols=device_settings.get("cols", 16), rows=device_settings.get("rows", 2))
        print(f"[{_ts()}] LCD ready (sim)")
    else:
        from sensors.lcd import I2CLCD
        lcd = I2CLCD(
            cols=device_settings.get("cols", 16),
            rows=device_settings.get("rows", 2),
            i2c_addr=device_settings.get("i2c_addr", "0x27")
        )
        print(f"[{_ts()}] LCD ready (I2C addr={device_settings.get('i2c_addr','0x27')})")

    registry["LCD"] = lcd