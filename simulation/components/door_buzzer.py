import time
import threading
from settings import *

def _ts():
    return time.strftime("%H:%M:%S")

def run_door_buzzer(device_settings, registry: dict, stop_event):
    """
    registry: dict u koji upisujemo instancu pod ključem 'DB'
    """
    if is_simulated(device_settings):
        from simulators.door_buzzer import SimDoorBuzzer
        buzzer = SimDoorBuzzer()
        print(f"[{_ts()}] DB ready (sim)")
    else:
        from sensors.door_buzzer import DoorBuzzer
        pin = device_settings["pin"]
        active_high = device_settings.get("active_high", True)
        buzzer = DoorBuzzer(pin, active_high=active_high)
        print(f"[{_ts()}] DB ready (GPIO pin={pin})")

    registry["DB"] = buzzer

def handle_db_command(cmd, registry: dict, stop_event):
    """
    Komande:
      db on
      db off
    """
    print("CLI ready. Type: help")

    buzzer = registry.get("DB")
    if buzzer is None:
        print("DB not configured.")
        return

    if len(cmd) < 2:
        print("Usage: db on | off ")
        return

    action = cmd[1]

    if action == "on":
        buzzer.on()
        print("DB: ON")

    elif action == "off":
        buzzer.off()
        print("DB: OFF")
        
    else:
        print("Unknown DB command")

