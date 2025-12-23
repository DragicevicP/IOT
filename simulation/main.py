
import threading
import time

from cli import cli_loop
from settings import load_settings
from components.door_sensor import run_door_sensor
from components.door_buzzer import run_door_buzzer
from components.ultrasonic import run_ultrasonic
from components.led import run_door_light
from components.door_motion_sensor import run_door_motion_sensor
from components.door_membrane_switch import run_door_membrane_switch


if __name__ == "__main__":
    print("Starting PI1 Door System")

    settings = load_settings()
    threads = []
    stop_event = threading.Event()

    registry = {}

    try:
        run_ultrasonic(settings["DUS1"], threads, stop_event)
        run_door_sensor(settings["DS1"], threads, stop_event)
        run_door_buzzer(settings["DB"], registry, stop_event)
        run_door_light(settings["DL"], registry, stop_event)
        run_door_motion_sensor(settings["DPIR1"], threads, stop_event)
        run_door_membrane_switch(settings["DMS"], threads, stop_event)

        cli_thread = threading.Thread(
            target=cli_loop,
            args=(registry, stop_event),
            daemon=True
        )
        cli_thread.start()

        while not stop_event.is_set():
            time.sleep(0.2)
            

    except KeyboardInterrupt:
        print("Stopping system")
        stop_event.set()
