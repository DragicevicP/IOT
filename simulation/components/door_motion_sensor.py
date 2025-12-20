import threading
import time
from simulators.door_motion_sensor import run_door_motion_simulator

def dpir1_callback(state):
    t = time.strftime('%H:%M:%S')
    status = "MOTION" if state else "NO MOTION"
    print(f"[{t}] DPIR1 Door Motion: {status}")

def run_door_motion_sensor(settings, threads, stop_event):
    delay = settings.get("poll_interval", 2)

    if settings["simulated"]:
        t = threading.Thread(
            target=run_door_motion_simulator,
            args=(delay, dpir1_callback, stop_event)
        )
    else:
        print("Starting DPIR1 GPIO sensor")
        from sensors.door_motion_sensor import DoorMotionSensor, run_door_motion_loop
        sensor = DoorMotionSensor(settings["pin"])
        t = threading.Thread(
            target=run_door_motion_loop,
            args=(sensor, delay, dpir1_callback, stop_event)
        )

    t.start()
    threads.append(t)
