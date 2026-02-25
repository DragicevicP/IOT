from functools import partial
import threading
import time

from settings import *
from mqtt.payload import build_payload
from mqtt.topics import sensor_topic

from simulators.gsg import run_gsg_simulator

def gsg_callback(state, system_info, mqtt_sender, device_id, simulated, event_bus):
    t = time.strftime('%H:%M:%S')
    status = "SHAKE" if state else "STILL"
    print(f"[{t}] {device_id} Gyro: {status} (simulated={simulated})")

    payload = build_payload(system_info, device_id, int(state), simulated)
    mqtt_sender.put(sensor_topic(system_info["pi"], device_id), payload)

    if event_bus is not None:
        from logic.events import DeviceEvent, now_ts
        event_bus.publish(DeviceEvent(
            device_id=device_id,
            value=int(state),
            simulated=simulated,
            timestamp=now_ts(),
            system_info=system_info
        ))


def run_gsg(device_settings, threads, stop_event, mqtt_sender, system_info, event_bus=None):
    delay = device_settings.get("poll_interval", 0.2)
    device_id = device_settings["id"]
    simulated = is_simulated(device_settings)

    callback = partial(
        gsg_callback,
        system_info=system_info,
        mqtt_sender=mqtt_sender,
        device_id=device_id,
        simulated=simulated,
        event_bus=event_bus
    )

    if simulated:
        t = threading.Thread(target=run_gsg_simulator, args=(delay, callback, stop_event), daemon=True)
    else:
        from sensors.gsg import GSGSensor, run_gsg_loop
        thr = float(device_settings.get("threshold_g", 0.35))
        sensor = GSGSensor(threshold_g=thr)
        t = threading.Thread(target=run_gsg_loop, args=(sensor, delay, callback, stop_event), daemon=True)

    t.start()
    threads.append(t)