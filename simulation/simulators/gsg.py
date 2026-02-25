import time
import random

def run_gsg_simulator(delay, callback, stop_event):
    while not stop_event.is_set():
        # 5% šanse da se desi “shake”
        shake = 1 if random.random() < 0.05 else 0
        callback(shake)
        time.sleep(delay)