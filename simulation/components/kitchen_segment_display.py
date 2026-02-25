import threading
from mqtt.topics import sensor_topic
from mqtt.payload import build_payload
from settings import *

def run_four_digit_display(device_settings, registry, stop_event):

    simulated = is_simulated(device_settings)

    if simulated:
        from simulators.kitchen_segment_display import SimulatedDisplay
        display = SimulatedDisplay()
    else:
        from sensors.kitchen_segment_display import FourDigitDisplay
        display = FourDigitDisplay(
            device_settings["segments"],
            device_settings["digits"]
        )

    registry["4SD"] = display


def handle_4sd_command(cmd, registry, stop_event):
    display = registry.get("4SD")

    if not display:
        print("4SD not configured.")
        return

    if len(cmd) < 2:
        print("Usage: 4sd 1234  |  4sd time")
        return

    arg = cmd[1]

    if arg == "time":
        import time
        value = time.strftime("%H%M")
    else:
        value = arg

    display.set_value(value)
    print(f"4SD: {value}")
    
    mqtt_sender = registry.get("_mqtt_sender")
    system_info = registry.get("_system")

    mqtt_sender.put(
        sensor_topic(system_info["pi"], "4SD"),
        build_payload(system_info, "4SD", value, True)
    )