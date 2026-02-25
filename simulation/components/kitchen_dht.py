from functools import partial
import threading
import time

from simulators.kitchen_dht import run_kitchen_dht_simulator
from settings import *
from mqtt.payload import build_payload
from mqtt.topics import sensor_topic


def kitchen_dht_callback(data, system_info, mqtt_sender, device_id, simulated):

    t = time.strftime('%H:%M:%S')

    if data.get("ok"):
        h = data["humidity"]
        temp = data["temperature"]
        value = f"H={h};T={temp}"
        print(f"[{t}] {device_id} Kitchen DHT: {value} (simulated={simulated})")
    else:
        value = f"ERR={data.get('code')}"
        print(f"[{t}] {device_id} Kitchen DHT ERROR {value}")

    payload = build_payload(system_info, device_id, value, simulated)
    topic = sensor_topic(system_info["pi"], device_id)
    mqtt_sender.put(topic, payload)


def run_kitchen_dht(device_settings, threads, stop_event, mqtt_sender, system_info):

    delay = device_settings.get("poll_interval", 2)
    device_id = device_settings["id"]
    simulated = is_simulated(device_settings)

    callback = partial(
        kitchen_dht_callback,
        system_info=system_info,
        mqtt_sender=mqtt_sender,
        device_id=device_id,
        simulated=simulated
    )

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