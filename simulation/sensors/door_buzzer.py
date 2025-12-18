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

    def beep(self, count: int = 1, on_ms: int = 200, off_ms: int = 200, stop_event=None):
        for _ in range(max(0, int(count))):
            if stop_event is not None and stop_event.is_set():
                break
            self.on()
            time.sleep(max(0, on_ms) / 1000.0)
            self.off()
            time.sleep(max(0, off_ms) / 1000.0)
