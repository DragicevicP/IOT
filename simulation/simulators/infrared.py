import time
import random

def run_infrared_simulator(delay, callback, stop_event):
    state = 0

    while True:
        if state == 0:
            if random.random() > 0.8:
                state = 1
        else:
            if random.random() > 0.3:
                state = 0

        callback(state)

        time.sleep(delay)
        if stop_event.is_set():
            break