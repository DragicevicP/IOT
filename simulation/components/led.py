import time
from settings import *


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
        print("DL: ON")

    elif action == "off":
        light.off()
        print("DL: OFF")

    else:
        print("Unknown DL command. Use: dl on | dl off")
