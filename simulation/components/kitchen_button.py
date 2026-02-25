# components/kitchen_button.py
from functools import partial
import threading
import time
from settings import *
from mqtt.payload import build_payload
from mqtt.topics import sensor_topic
from simulators.kitchen_button import run_kitchen_button_simulator


def kitchen_button_callback(state, system_info, mqtt_sender, device_id, simulated):
    t = time.strftime('%H:%M:%S')

    status = "PRESSED" if state else "RELEASED"
    print(f"[{t}] {device_id} Kitchen Button: {status} (simulated={simulated})")

    payload = build_payload(system_info, device_id, status, simulated)
    topic = sensor_topic(system_info["pi"], device_id)
    mqtt_sender.put(topic, payload)


def run_kitchen_button(device_settings, threads, stop_event, mqtt_sender, system_info):
    delay = device_settings.get("poll_interval", 0.2)
    device_id = device_settings["id"]
    simulated = is_simulated(device_settings)

    callback = partial(
        kitchen_button_callback,
        system_info=system_info,
        mqtt_sender=mqtt_sender,
        device_id=device_id,
        simulated=simulated
    )

    if simulated:
        t = threading.Thread(
            target=run_kitchen_button_simulator,
            args=(delay, callback, stop_event),
            daemon=True
        )
    else:
        from sensors.kitchen_button import KitchenButton, run_kitchen_button_loop
        sensor = KitchenButton(device_settings["pin"])
        t = threading.Thread(
            target=run_kitchen_button_loop,
            args=(sensor, delay, callback, stop_event),
            daemon=True
        )

    t.start()
    threads.append(t)