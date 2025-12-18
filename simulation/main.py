
import threading
import time
from settings import load_settings
from components.door_sensor import run_door_sensor
from components.door_buzzer import run_door_buzzer, start_buzzer_cli
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

    registry = {}  #ovde drzimo aktuator instance

    try:
        run_door_sensor(settings["DS1"], threads, stop_event)

        run_door_buzzer(settings["DB"], registry, stop_event)

        #CLI za kontrolu DB
        cli_thread = threading.Thread(target=start_buzzer_cli, args=(registry, stop_event), daemon=True)
        cli_thread.start()

        while not stop_event.is_set():
            time.sleep(0.2)
            
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping system")
        stop_event.set()
