from functools import partial
import threading
import time
from simulators.ultrasonic import run_ultrasonic_simulator
from settings import *
from mqtt.payload import build_payload
from mqtt.topics import sensor_topic

def ultrasonic_callback(distance, system_info, mqtt_sender, device_id, simulated):
    payload = build_payload(system_info, device_id, distance, simulated)

    topic = sensor_topic(system_info["pi_id"], device_id)
    mqtt_sender.put(topic, payload)

    t = time.strftime('%H:%M:%S')
    print(f"[{t}] {device_id} Ultrasonic: {distance} cm (simulated={simulated})")


def run_ultrasonic(device_settings, threads, stop_event, mqtt_sender, system_info):
    delay = device_settings.get("poll_interval", 2)
    device_id = device_settings["id"]
    simulated = is_simulated(device_settings)

    callback = partial(ultrasonic_callback, system_info=system_info, mqtt_sender=mqtt_sender, device_id=device_id, simulated=simulated)

    if is_simulated(device_settings):
        t = threading.Thread(target=run_ultrasonic_simulator, args=(delay, callback, stop_event), daemon=True)
    else:
        from sensors.ultrasonic import UltrasonicSensor, run_ultrasonic_loop
        sensor = UltrasonicSensor()
        t = threading.Thread(target=run_ultrasonic_loop, args=(sensor, delay, callback, stop_event), daemon=True)

    t.start()
    threads.append(t)