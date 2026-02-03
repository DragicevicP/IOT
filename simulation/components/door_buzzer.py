import time
import threading
from settings import *
from mqtt.topics import sensor_topic
from mqtt.payload import build_payload
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
        value = 1
        print("DB: ON")

    elif action == "off":
        buzzer.off()
        value = 0
        print("DB: OFF")

    else:
        print("Unknown DB command")
        return

    mqtt_sender = registry.get("_mqtt_sender")
    system_info = registry.get("_system")

    mqtt_sender.put(
        sensor_topic(system_info["pi_id"], "DB"),
        build_payload(system_info, "DB", value, True)
    )

