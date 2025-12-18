import time

class UltrasonicSensor:
    def __init__(self):
        pass  

    def read_distance(self):
        return 0.0  

def run_ultrasonic_loop(sensor, delay, callback, stop_event):
    while True:
        distance = sensor.read_distance()
        callback(distance)

        time.sleep(delay)
        if stop_event.is_set():
            break