import time

def run_door_sensor_simulator(delay, callback, stop_event):
    t0 = time.time()

    cycle = 14.0   # ukupno trajanje ciklusa (sek)
    closed1 = 4.0  # zatvoreno
    open_long = 10.0  # otvoreno dovoljno dugo da upali alarm (>5s)
    # ostatak ciklusa opet zatvoreno

    while not stop_event.is_set():
        dt = (time.time() - t0) % cycle

        if dt < closed1:
            state = 0          
        elif dt < closed1 + open_long:
            state = 1        
        else:
            state = 0          

        callback(state)
        time.sleep(delay)