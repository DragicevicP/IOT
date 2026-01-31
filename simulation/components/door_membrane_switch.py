from functools import partial
import threading
import time
from simulators.door_membrane_switch import run_dms_simulator
from settings import *
from mqtt.payload import build_payload
from mqtt.topics import sensor_topic

def dms_callback(state, system_info, mqtt_sender, device_id, simulated):
    t = time.strftime('%H:%M:%S')
    status = "PRESSED" if state else "RELEASED"
    print(f"[{t}] {device_id} Door Membrane Switch: {status} (simulated={simulated})")
    
    payload = build_payload(system_info, device_id, status, simulated)

    topic = sensor_topic(system_info["pi_id"], device_id)
    mqtt_sender.put(topic, payload)

def run_door_membrane_switch(device_settings, threads, stop_event, mqtt_sender, system_info):
    delay = device_settings.get("poll_interval", 2)
    device_id = device_settings["id"]
    simulated = is_simulated(device_settings)

    callback = partial(dms_callback, system_info=system_info, mqtt_sender=mqtt_sender, device_id=device_id, simulated=simulated)

    if is_simulated(device_settings):
        t = threading.Thread(target=run_dms_simulator, args=(delay, callback, stop_event), daemon=True)
    else:
        from sensors.door_membrane_switch import DoorMembraneSwitch, run_dms_loop
        sensor = DoorMembraneSwitch(device_settings["pin"])
        t = threading.Thread(target=run_dms_loop, args=(sensor, delay, callback, stop_event), daemon=True)

    t.start()
    threads.append(t)
