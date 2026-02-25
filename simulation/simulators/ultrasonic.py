import time
import random

def run_ultrasonic_simulator(delay, callback, stop_event):
    base_far = 185.0
    current = base_far

    mode = "idle"        
    target_min = 45.0
    step = 12.0

    next_pass_in = random.uniform(15, 30)  
    last = time.time()

    while True:
        if stop_event.is_set():
            break

        now = time.time()
        dt = now - last
        last = now

        if mode == "idle":
            next_pass_in -= dt
            current = base_far + random.uniform(-6, 6)

            if next_pass_in <= 0:
                mode = "approaching"
                step = random.uniform(20, 35)

        elif mode == "approaching":
            current -= step
            current += random.uniform(-2, 2)
            if current <= target_min:
                current = target_min + random.uniform(-2, 2)
                mode = "leaving"
                step = random.uniform(8, 18)

        elif mode == "leaving":
            current += step
            current += random.uniform(-2, 2)
            if current >= base_far:
                current = base_far + random.uniform(-6, 6)
                mode = "idle"
                next_pass_in = random.uniform(15, 30)

        distance = int(max(15, min(200, round(current))))
        callback(distance)
        time.sleep(delay)

        time.sleep(delay)