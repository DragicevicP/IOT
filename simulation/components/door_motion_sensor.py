from functools import partial
import threading
import time
from simulators.door_motion_sensor import run_door_motion_simulator
from settings import *
from mqtt.payload import build_payload
from mqtt.topics import sensor_topic
from logic.events import DeviceEvent, now_ts

def door_motion_callback(state, system_info, mqtt_sender, device_id, simulated, event_bus=None):
    t = time.strftime('%H:%M:%S')
    status = "MOTION" if state else "NO MOTION"
    print(f"[{t}] {device_id}  Door Motion: {status} (simulated={simulated})")

    payload = build_payload(system_info, device_id, status, simulated)

    topic = sensor_topic(system_info["pi"], device_id)
    mqtt_sender.put(topic, payload)

    if event_bus is not None:
        event_bus.publish(DeviceEvent(
            device_id=device_id,
            value=state,              
            simulated=simulated,
            timestamp=now_ts(),
            system_info=system_info
        ))

def run_door_motion_sensor(device_settings, threads, stop_event, mqtt_sender, system_info, event_bus=None):
    delay = device_settings.get("poll_interval", 2)
    device_id = device_settings["id"]
    simulated = is_simulated(device_settings)

    callback = partial(door_motion_callback, system_info=system_info, mqtt_sender=mqtt_sender, device_id=device_id, simulated=simulated, event_bus=event_bus)

    if is_simulated(device_settings):
        t = threading.Thread(target=run_door_motion_simulator, args=(delay, callback, stop_event), daemon=True)
    else:
        from sensors.door_motion_sensor import DoorMotionSensor, run_door_motion_loop
        sensor = DoorMotionSensor(device_settings["pin"])
        t = threading.Thread(target=run_door_motion_loop, args=(sensor, delay, callback, stop_event), daemon=True)

    t.start()
    threads.append(t)
