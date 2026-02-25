from functools import partial
import threading
import time

from simulators.kitchen_dht import run_kitchen_dht_simulator
from settings import *
from mqtt.payload import build_payload
from mqtt.topics import sensor_topic

from logic.events import DeviceEvent, now_ts  # :contentReference[oaicite:2]{index=2}

def kitchen_dht_callback(data, system_info, mqtt_sender, device_id, simulated, event_bus):
    t = time.strftime('%H:%M:%S')

    if event_bus is not None:
        event_bus.publish(DeviceEvent(
            device_id=device_id,
            value=data,               
            simulated=simulated,
            timestamp=now_ts(),
            system_info=system_info
        ))

    
    if data.get("ok"):
        h = float(data["humidity"])
        temp = float(data["temperature"])

        print(f"[{t}] {device_id} Kitchen DHT: H={h};T={temp} (simulated={simulated})")

        payload = build_payload(system_info, device_id, f"H={h};T={temp}", simulated)
        mqtt_sender.put(sensor_topic(system_info["pi"], device_id), payload)
    else:
        value = f"ERR={data.get('code')}"
        print(f"[{t}] {device_id} Kitchen DHT ERROR {value}")
        payload = build_payload(system_info, device_id, value, simulated)
        mqtt_sender.put(sensor_topic(system_info["pi"], device_id), payload)


def run_kitchen_dht(device_settings, threads, stop_event, mqtt_sender, system_info, event_bus=None):
    delay = device_settings.get("poll_interval", 2)
    device_id = device_settings["id"]
    simulated = is_simulated(device_settings)

    callback = partial(kitchen_dht_callback, system_info=system_info, mqtt_sender=mqtt_sender, device_id=device_id, simulated=simulated, event_bus=event_bus)

    if simulated:
        t = threading.Thread(
            target=run_kitchen_dht_simulator,
            args=(delay, callback, stop_event),
            daemon=True
        )
    else:
        from sensors.kitchen_dht import DHTSensor, run_dht_loop
        sensor = DHTSensor(device_settings["pin"])
        t = threading.Thread(
            target=run_dht_loop,
            args=(sensor, delay, callback, stop_event),
            daemon=True
        )

    t.start()
    threads.append(t)