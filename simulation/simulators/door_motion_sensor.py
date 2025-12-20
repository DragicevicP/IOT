import time
import random

def run_door_motion_simulator(delay, callback, stop_event):
    state = 0  # nema pokreta

    while True:
        # PIR: obično se javi "spike" pokreta, pa se vrati na 0
        if random.random() > 0.8:
            state = 1
        else:
            state = 0

        callback(state)

        time.sleep(delay)
        if stop_event.is_set():
            break
