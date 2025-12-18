
import threading
import time
from settings import load_settings
from components.door_sensor import run_door_sensor
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass


if __name__ == "__main__":
    print("Starting PI1 Door System")

    settings = load_settings()
    threads = []
    stop_event = threading.Event()

    try:
        run_door_sensor(settings["DS1"], threads, stop_event)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping system")
        stop_event.set()
