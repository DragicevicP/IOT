from functools import partial
import threading
import time

from simulators.door_membrane_switch import run_dms_simulator
from settings import is_simulated
from mqtt.payload import build_payload
from mqtt.topics import sensor_topic


def dms_key_callback(key, system_info, mqtt_sender, device_id, simulated, state):
    t = time.strftime('%H:%M:%S')

    if key == '*':
        state["buf"] = ""
        status = "PIN_CANCEL"
        print(f"[{t}] {device_id} Keypad: CANCEL (simulated={simulated})")

    elif key == '#':
        entered = state["buf"]
        state["buf"] = ""

        if entered == state["pin_code"]:
            status = "PIN_OK"
            print(f"[{t}] {device_id} Keypad: PIN_OK (simulated={simulated})")
        else:
            status = "PIN_BAD"
            print(f"[{t}] {device_id} Keypad: PIN_BAD (entered='{entered}', simulated={simulated})")

    else:
        if len(state["buf"]) < state["max_len"]:
            state["buf"] += key
        status = "PIN_INPUT"
        print(f"[{t}] {device_id} Keypad: key='{key}' buf='{state['buf']}' (simulated={simulated})")

    payload = build_payload(system_info, device_id, status, simulated)
    topic = sensor_topic(system_info["pi"], device_id)
    mqtt_sender.put(topic, payload)


def run_door_membrane_switch(device_settings, threads, stop_event, mqtt_sender, system_info):
    delay = device_settings.get("poll_interval", 0.05)
    device_id = device_settings["id"]
    simulated = is_simulated(device_settings)

    state = {"buf": "", "pin_code": str(device_settings.get("pin_code", "1234")), "max_len": int(device_settings.get("max_len", 8)),}

    callback = partial(dms_key_callback, system_info=system_info, mqtt_sender=mqtt_sender, device_id=device_id, simulated=simulated, state=state)

    if simulated:
        t = threading.Thread(target=run_dms_simulator, args=(delay, callback, stop_event), daemon=True)
    else:
        from sensors.door_membrane_switch import DoorMembraneSwitchKeypad, run_dms_loop

        rows = device_settings["rows"]
        cols = device_settings["cols"]

        keypad = DoorMembraneSwitchKeypad(rows=rows, cols=cols)
        t = threading.Thread(target=run_dms_loop, args=(keypad, delay, callback, stop_event), daemon=True)

    t.start()
    threads.append(t)