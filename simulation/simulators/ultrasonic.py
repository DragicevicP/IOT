import time
import random

def run_ultrasonic_simulator(delay, callback, stop_event):
    while True:
        distance = round(random.uniform(10, 200))
        callback(distance)

        time.sleep(delay)
        if stop_event.is_set():
            break