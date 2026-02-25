import time
from settings import *
from mqtt.topics import sensor_topic
from mqtt.payload import build_payload


def _ts():
    return time.strftime("%H:%M:%S")

def run_door_light(device_settings, registry: dict, stop_event):
    if is_simulated(device_settings):
        from simulators.led import SimLed
        led = SimLed()
        print(f"[{_ts()}] DL ready (sim)")
    else:
        from sensors.led import Led
        led = Led(device_settings["pin"])
        print(f"[{_ts()}] DL ready (GPIO pin={device_settings['pin']})")
    registry["DL"] = led
    registry["_DL_simulated"] = is_simulated(device_settings) 

def publish_dl_state(registry: dict, value: int, simulated: bool | None = None):
    mqtt_sender = registry.get("_mqtt_sender")
    system_info = registry.get("_system")
    if not mqtt_sender or not system_info:
        return

    if simulated is None:
        simulated = bool(registry.get("_DL_simulated", True))

    mqtt_sender.put(
        sensor_topic(system_info["pi"], "DL"),
        build_payload(system_info, "DL", value, simulated)
    )

def handle_dl_command(cmd, registry, stop_event):
    light = registry.get("DL")
    if not light:
        print("DL not configured.")
        return

    if len(cmd) < 2:
        print("Usage: dl on | dl off")
        return

    action = cmd[1]

    if action == "on":
        light.on()
        value = 1
        print("DL: ON")
        publish_dl_state(registry, 1)


    elif action == "off":
        light.off()
        value = 0
        print("DL: OFF")
        publish_dl_state(registry, 0)

    else:
        print("Unknown DL command.")
        return

