import threading
import time
from simulators.door_sensor import run_door_sensor_simulator
from settings import *

def door_sensor_callback(state):
    t = time.strftime('%H:%M:%S')
    status = "OPEN" if state else "CLOSED"
    print(f"[{t}] DS1 Door Sensor: {status}")

def run_door_sensor(device_settings, threads, stop_event):
    delay = device_settings.get("poll_interval", 2)

    if is_simulated(device_settings):
        t = threading.Thread(
            target=run_door_sensor_simulator,
            args=(delay, door_sensor_callback, stop_event)
        )
    else:
        print("Starting DS1 GPIO sensor")
        from sensors.door_sensor import DoorSensor, run_door_sensor_loop
        sensor = DoorSensor(device_settings["pin"])
        t = threading.Thread(
            target=run_door_sensor_loop,
            args=(sensor, delay, door_sensor_callback, stop_event)
        )

    t.start()
    threads.append(t)