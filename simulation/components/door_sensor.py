from functools import partial
import threading
import time
from simulators.door_sensor import run_door_sensor_simulator
from settings import *
from mqtt.payload import build_payload
from mqtt.topics import sensor_topic

def door_sensor_callback(state, system_info, mqtt_sender, device_id, simulated):
    t = time.strftime('%H:%M:%S')
    status = "OPEN" if state else "CLOSED"
    print(f"[{t}] {device_id} Door Sensor: {status} (simulated={simulated})")

    payload = build_payload(system_info, device_id, status, simulated)

    topic = sensor_topic(system_info["pi"], device_id)
    mqtt_sender.put(topic, payload)


def run_door_sensor(device_settings, threads, stop_event, mqtt_sender, system_info):
    delay = device_settings.get("poll_interval", 2)
    device_id = device_settings["id"]
    simulated = is_simulated(device_settings)

    callback = partial(door_sensor_callback, system_info=system_info, mqtt_sender=mqtt_sender, device_id=device_id, simulated=simulated)

    if is_simulated(device_settings):
        t = threading.Thread(target=run_door_sensor_simulator, args=(delay, callback, stop_event), daemon=True)
    else:
        from sensors.door_sensor import DoorSensor, run_door_sensor_loop
        sensor = DoorSensor(device_settings["pin"])
        t = threading.Thread(target=run_door_sensor_loop, args=(sensor, delay, callback, stop_event), daemon=True)

    t.start()
    threads.append(t)