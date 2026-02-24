import RPi.GPIO as GPIO
import time


class InfraredSensor:
    def __init__(self, pin: int):
        GPIO.setmode(GPIO.BCM)
        self.pin = pin
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def read(self) -> int:
        return GPIO.input(self.pin)


def run_infrared_loop(sensor: InfraredSensor, delay: float, callback, stop_event):
    while True:
        state = sensor.read()
        callback(state)

        time.sleep(delay)
        if stop_event.is_set():
            break