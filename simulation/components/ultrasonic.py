import threading
import time
from simulators.ultrasonic import run_ultrasonic_simulator
from settings import *

def ultrasonic_callback(distance):
    t = time.strftime('%H:%M:%S')
    print(f"[{t}] DUS1 Distance: {distance} cm")

def run_ultrasonic(device_settings, threads, stop_event):
    delay = device_settings.get("poll_interval", 2)

    if is_simulated(device_settings):
        t = threading.Thread(
            target=run_ultrasonic_simulator,
            args=(delay, ultrasonic_callback, stop_event)
        )
    else:
        print("Starting DUS1 sensor")
        from sensors.ultrasonic import UltrasonicSensor, run_ultrasonic_loop
        sensor = UltrasonicSensor()
        t = threading.Thread(
            target=run_ultrasonic_loop,
            args=(sensor, delay, ultrasonic_callback, stop_event)
        )

    t.start()
    threads.append(t)