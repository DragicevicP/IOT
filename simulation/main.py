
import threading
import time

from cli import cli_loop
from settings import *
from components.door_sensor import run_door_sensor
from components.door_buzzer import run_door_buzzer
from components.ultrasonic import run_ultrasonic
from components.led import run_door_light
from components.door_motion_sensor import run_door_motion_sensor
from components.door_membrane_switch import run_door_membrane_switch


if __name__ == "__main__":
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    registry = {}

    system_info = settings["system"]
    print(f"Starting {system_info['device_name']} on {system_info['pi_id']}")

    try:
        run_door_sensor(get_device_settings(settings, "DS1"),threads,stop_event)
        run_ultrasonic(get_device_settings(settings, "DUS1"), threads, stop_event)
        run_door_buzzer(get_device_settings(settings, "DB"), registry, stop_event)
        run_door_light(get_device_settings(settings, "DL"), registry, stop_event)
        run_door_motion_sensor(get_device_settings(settings, "DPIR1"), threads, stop_event)
        run_door_membrane_switch(get_device_settings(settings, "DMS"), threads, stop_event)

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
