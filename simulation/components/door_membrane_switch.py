import threading
import time
from simulators.door_membrane_switch import run_dms_simulator

def dms_callback(state):
    t = time.strftime('%H:%M:%S')
    status = "PRESSED" if state else "RELEASED"
    print(f"[{t}] DMS Door Membrane Switch: {status}")

def run_door_membrane_switch(settings, threads, stop_event):
    delay = settings.get("poll_interval", 2)

    if settings.get("simulated", True):
        t = threading.Thread(
            target=run_dms_simulator,
            args=(delay, dms_callback, stop_event)
        )
    else:
        from sensors.door_membrane_switch import DoorMembraneSwitch, run_dms_loop
        sensor = DoorMembraneSwitch(settings["pin"])
        t = threading.Thread(
            target=run_dms_loop,
            args=(sensor, delay, dms_callback, stop_event)
        )

    t.start()
    threads.append(t)
