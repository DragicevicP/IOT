import time
import random

def run_kitchen_dht_simulator(delay, callback, stop_event):
    humidity = 45
    temperature = 23.0

    while True:
        humidity += random.randint(-2, 2)
        temperature += random.uniform(-0.3, 0.3)

        humidity = max(20, min(80, humidity))
        temperature = max(10.0, min(40.0, temperature))

        if random.random() < 0.05:
            data = {"ok": False, "code": -2, "humidity": -999, "temperature": -999}
        else:
            data = {"ok": True, "code": 0, "humidity": humidity, "temperature": round(temperature, 1)}

        callback(data)

        time.sleep(delay)
        if stop_event.is_set():
            break