# simulators/kitchen_button.py
import time
import random

def run_kitchen_button_simulator(delay, callback, stop_event):
    state = 0
    while True:
        if random.random() > 0.7:
            state = 1 - state  
            
        callback(state)

        time.sleep(delay)
        if stop_event.is_set():
            break