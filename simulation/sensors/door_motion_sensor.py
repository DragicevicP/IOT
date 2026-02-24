import RPi.GPIO as GPIO
import time

class DoorMotionSensor:
    def __init__(self, pin):
        GPIO.setmode(GPIO.BCM)  
        self.pin = pin
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def read(self):
        return GPIO.input(self.pin)

def run_door_motion_loop(sensor, delay, callback, stop_event):
    while True:
        state = sensor.read()
        callback(state)

        time.sleep(delay)
        if stop_event.is_set():
            break
