import time
import random

def run_dms_simulator(delay, callback, stop_event):
    state = 0

    while True:
        # simulira kratko pritiskanje tastera
        if random.random() > 0.85:
            state = 1
        else:
            state = 0

        callback(state)

        time.sleep(delay)
        if stop_event.is_set():
            break
