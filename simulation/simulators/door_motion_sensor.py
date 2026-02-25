import time
import random

def run_door_motion_simulator(delay, callback, stop_event):
    state = 0 

    while True:
        if random.random() > 0.9:
            state = 1
        else:
            state = 0

        callback(state)

        time.sleep(delay)
        if stop_event.is_set():
            break
