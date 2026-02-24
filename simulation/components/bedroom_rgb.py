# components/brgb.py
import time
from settings import is_simulated
from mqtt.topics import sensor_topic
from mqtt.payload import build_payload

def _ts():
    return time.strftime("%H:%M:%S")

def run_bedroom_rgb(device_settings, registry: dict, stop_event):
    """
    Inicijalizuje BRGB (sim ili pravi GPIO) i upisuje ga u registry["BRGB"].
    """
    if is_simulated(device_settings):
        from simulators.bedroom_rgb import SimBedroomRGB
        brgb = SimBedroomRGB()
        print(f"[{_ts()}] BRGB ready (sim)")
    else:
        from sensors.bedroom_rgb import BedroomRGB
        brgb = BedroomRGB(
            red_pin=device_settings["red_pin"],
            green_pin=device_settings["green_pin"],
            blue_pin=device_settings["blue_pin"],
            active_high=device_settings.get("active_high", True)
        )
        print(f"[{_ts()}] BRGB ready (GPIO R={device_settings['red_pin']} G={device_settings['green_pin']} B={device_settings['blue_pin']})")

    registry["BRGB"] = brgb


def handle_brgb_command(cmd, registry, stop_event):
    brgb = registry.get("BRGB")
    if not brgb:
        print("BRGB not configured.")
        return

    if len(cmd) < 2:
        print("Usage: brgb <off|white|red|green|blue|yellow|purple|lightblue> | brgb rgb <r> <g> <b>")
        return

    action = cmd[1].lower()
    value = None

    if action == "off":
        brgb.off()
        value = "OFF"
        print("BRGB: OFF")

    elif action in ("white", "red", "green", "blue", "yellow", "purple"):
        if action in ("light_blue", "cyan"):
            action = "lightblue"

        brgb.set_color_name(action)
        value = action.upper()
        print(f"BRGB: {value}")

    elif action == "rgb":
        if len(cmd) != 5:
            print("Usage: brgb rgb <r> <g> <b>  (values: 0/1)")
            return
        try:
            r = int(cmd[2]); g = int(cmd[3]); b = int(cmd[4])
        except ValueError:
            print("RGB values must be integers 0 or 1.")
            return

        brgb.set_rgb(r, g, b)
        value = f"RGB({int(bool(r))},{int(bool(g))},{int(bool(b))})"
        print(f"BRGB: {value}")

    else:
        print("Unknown BRGB command.")
        return

    mqtt_sender = registry.get("_mqtt_sender")
    system_info = registry.get("_system")

    if mqtt_sender and system_info:
        mqtt_sender.put(
            sensor_topic(system_info["pi_id"], "BRGB"),
            build_payload(system_info, "BRGB", value, True)
        )


def map_ir_key_to_brgb_command(ir_key: str):
    k = (ir_key or "").strip().upper()

    mapping = {
        "KEY_POWER": {"on": False},   
        "KEY_1": "red",
        "KEY_2": "green",
        "KEY_3": "blue",
        "KEY_4": "white",
        "KEY_5": "yellow",
        "KEY_6": "purple",
        "KEY_0": "off",
    }
    return mapping.get(k)