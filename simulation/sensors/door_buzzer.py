import time
import RPi.GPIO as GPIO

class DoorBuzzer:
    def __init__(self, pin: int, active_high: bool = True):
        self.pin = pin
        self.active_high = active_high
        GPIO.setup(pin, GPIO.OUT)
        self.off()

    def on(self):
        GPIO.output(self.pin, GPIO.HIGH if self.active_high else GPIO.LOW)

    def off(self):
        GPIO.output(self.pin, GPIO.LOW if self.active_high else GPIO.HIGH)

   