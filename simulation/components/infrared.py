from functools import partial
import threading
import time

from settings import is_simulated
from mqtt.payload import build_payload
from mqtt.topics import sensor_topic
from simulators.infrared import run_infrared_simulator


def infrared_callback(state, system_info, mqtt_sender, device_id, simulated):
    t = time.strftime('%H:%M:%S')
    status = "DETECTED" if state else "CLEAR"
    print(f"[{t}] {device_id} Infrared: {status} (simulated={simulated})")

    payload = build_payload(system_info, device_id, status, simulated)
    topic = sensor_topic(system_info["pi"], device_id)
    mqtt_sender.put(topic, payload)


def run_infrared(device_settings, threads, stop_event, mqtt_sender, system_info):
    delay = device_settings.get("poll_interval", 2)
    device_id = device_settings["id"]
    simulated = is_simulated(device_settings)

    callback = partial(infrared_callback, system_info=system_info, mqtt_sender=mqtt_sender, device_id=device_id, simulated=simulated)

    if simulated:
        t = threading.Thread(target=run_infrared_simulator, args=(delay, callback, stop_event), daemon=True)
    else:
        from sensors.infrared import InfraredSensor, run_infrared_loop
        sensor = InfraredSensor(device_settings["pin"])
        t = threading.Thread(target=run_infrared_loop, args=(sensor, delay, callback, stop_event), daemon=True)

    t.start()
    threads.append(t)