import argparse
import threading
import time

from cli import cli_loop
from settings import load_settings, get_device_settings, get_mqtt_settings

from components.door_sensor import run_door_sensor
from components.door_buzzer import run_door_buzzer
from components.ultrasonic import run_ultrasonic
from components.led import run_door_light
from components.door_motion_sensor import run_door_motion_sensor
from components.door_membrane_switch import run_door_membrane_switch

from components.kitchen_dht import run_kitchen_dht
from components.kitchen_segment_display import run_four_digit_display
from components.kitchen_button import run_kitchen_button

from components.infrared import run_infrared
from components.bedroom_rgb import run_bedroom_rgb

from mqtt.mqtt_client import MQTTClient
from mqtt.batch_sender import MQTTSenderDaemon
from logic.engine import LogicEngine
from logic.event_bus import EventBus


def parse_args(system_cfg: dict):
    default_pi = system_cfg.get("default_run", "PI1")
    p = argparse.ArgumentParser()
    p.add_argument(
        "--pi",
        default=default_pi,
        help="Run on: all | PI1 | PI2 | PI3 | PI1,PI3"
    )
    return p.parse_args()


def selected_pis(pi_arg: str):
    pi_arg = (pi_arg or "").strip()
    if pi_arg.lower() == "all":
        return None  # None => all enabled
    return {x.strip().upper() for x in pi_arg.split(",") if x.strip()}


def device_enabled(settings: dict, device_id: str, chosen: set | None) -> bool:
    devices = settings.get("devices", {})

    if device_id not in devices:
        return False
    if chosen is None:
        return True

    dev_pi = devices[device_id].get("pi_id")

    if not dev_pi:
        return True

    return dev_pi.upper() in chosen


def system_info_for_run(settings: dict, chosen: set | None):
    system_cfg = settings.get("system", {})
    profiles = system_cfg.get("pis", {})

    if chosen is None:
        pi_list = [p.upper() for p in system_cfg.get("available_pis", ["PI1", "PI2", "PI3"])]
    else:
        pi_list = sorted(chosen)

    names = []
    locs = []

    for pi in pi_list:
        prof = profiles.get(pi, {})
        names.append(prof.get("device_name", f"{pi}System"))
        locs.append(prof.get("location", pi))

    return {
        "pi": ",".join(pi_list),
        "device_name": " + ".join(names),
        "location": " + ".join(locs)
    }


if __name__ == "__main__":
    settings = load_settings()
    system_cfg = settings.get("system", {})

    args = parse_args(system_cfg)
    chosen = selected_pis(args.pi)

    sys_info = system_info_for_run(settings, chosen)
    print(f"Starting {sys_info['device_name']} ({sys_info['location']}) | selected={args.pi}")

    threads = []
    stop_event = threading.Event()
    registry = {}

    mqtt_cfg = get_mqtt_settings(settings)
    mqtt_client = MQTTClient(mqtt_cfg["host"], mqtt_cfg["port"])

    mqtt_sender = MQTTSenderDaemon(
        mqtt_client,
        batch_size=mqtt_cfg.get("batch_size", 10),
        flush_interval=mqtt_cfg.get("flush_interval", 2.0)
    )

    registry["_mqtt_sender"] = mqtt_sender
    registry["_system"] = sys_info

    threading.Thread(target=mqtt_sender.run, args=(stop_event,), daemon=True).start()

    event_bus = EventBus()
    logic_engine = LogicEngine(settings=settings, registry=registry, bus=event_bus)
    threading.Thread(target=logic_engine.run_loop, args=(stop_event,), daemon=True).start()


    try:
        # PI1 devices
        if device_enabled(settings, "DL", chosen):
            run_door_light(get_device_settings(settings, "DL"), registry, stop_event)

        if device_enabled(settings, "DS1", chosen):
            run_door_sensor(get_device_settings(settings, "DS1"), threads, stop_event, mqtt_sender, sys_info, event_bus)

        if device_enabled(settings, "DUS1", chosen):
            run_ultrasonic(get_device_settings(settings, "DUS1"), threads, stop_event, mqtt_sender, sys_info, event_bus)

        if device_enabled(settings, "DPIR1", chosen):
            run_door_motion_sensor(get_device_settings(settings, "DPIR1"), threads, stop_event, mqtt_sender, sys_info, event_bus)

        if device_enabled(settings, "DMS", chosen):
            run_door_membrane_switch(get_device_settings(settings, "DMS"), threads, stop_event, mqtt_sender, sys_info, event_bus)

        if device_enabled(settings, "DB", chosen):
            run_door_buzzer(get_device_settings(settings, "DB"), registry, stop_event)

        # PI2 devices

        if device_enabled(settings, "DS2", chosen):
            run_door_sensor(get_device_settings(settings, "DS2"), threads, stop_event, mqtt_sender, sys_info, event_bus)

        if device_enabled(settings, "DUS2", chosen):
            run_ultrasonic(get_device_settings(settings, "DUS2"), threads, stop_event, mqtt_sender, sys_info, event_bus)

        if device_enabled(settings, "DPIR2", chosen):
            run_door_motion_sensor(get_device_settings(settings, "DPIR2"), threads, stop_event, mqtt_sender, sys_info, event_bus)

        if device_enabled(settings, "DHT3", chosen):
            run_kitchen_dht(get_device_settings(settings, "DHT3"), threads, stop_event, mqtt_sender, sys_info)

        if device_enabled(settings, "4SD", chosen):
            run_four_digit_display(get_device_settings(settings, "4SD"), registry, stop_event)

        if device_enabled(settings, "BTN", chosen):
            run_kitchen_button(get_device_settings(settings, "BTN"), threads, stop_event, mqtt_sender, sys_info)

        # PI3 devices
        if device_enabled(settings, "IR", chosen):
            run_infrared(get_device_settings(settings, "IR"), threads, stop_event, mqtt_sender, sys_info)

        if device_enabled(settings, "BRGB", chosen):
            run_bedroom_rgb(get_device_settings(settings, "BRGB"), registry, stop_event)

        if device_enabled(settings, "DPIR3", chosen):
            run_door_motion_sensor(get_device_settings(settings, "DPIR3"), threads, stop_event, mqtt_sender, sys_info, event_bus)


        threading.Thread(target=cli_loop, args=(registry, stop_event), daemon=True).start()

        while not stop_event.is_set():
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("Stopping system")
        stop_event.set()