# sensors/brgb.py
import RPi.GPIO as GPIO

class BedroomRGB:
    def __init__(self, red_pin: int, green_pin: int, blue_pin: int, active_high: bool = True):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin
        self.active_high = active_high

        GPIO.setup(self.red_pin, GPIO.OUT)
        GPIO.setup(self.green_pin, GPIO.OUT)
        GPIO.setup(self.blue_pin, GPIO.OUT)

        self.off()

    def _write(self, pin: int, on: bool):
        # active_high=True  -> ON = GPIO.HIGH
        # active_high=False -> ON = GPIO.LOW (npr. common anode)
        if self.active_high:
            GPIO.output(pin, GPIO.HIGH if on else GPIO.LOW)
        else:
            GPIO.output(pin, GPIO.LOW if on else GPIO.HIGH)

    def set_rgb(self, r: int, g: int, b: int):
        self._write(self.red_pin, bool(r))
        self._write(self.green_pin, bool(g))
        self._write(self.blue_pin, bool(b))

    def off(self):
        self.set_rgb(0, 0, 0)

    # boje (isto kao sa vežbi)
    def white(self):     self.set_rgb(1, 1, 1)
    def red(self):       self.set_rgb(1, 0, 0)
    def green(self):     self.set_rgb(0, 1, 0)
    def blue(self):      self.set_rgb(0, 0, 1)
    def yellow(self):    self.set_rgb(1, 1, 0)
    def purple(self):    self.set_rgb(1, 0, 1)


    def set_color_name(self, name: str):
        name = (name or "").strip().lower()

        if name in ("off", "0", "false"):
            self.off()
        elif name in ("white", "w"):
            self.white()
        elif name in ("red", "r"):
            self.red()
        elif name in ("green", "g"):
            self.green()
        elif name in ("blue", "b"):
            self.blue()
        elif name in ("yellow", "y"):
            self.yellow()
        elif name in ("purple", "p", "magenta"):
            self.purple()
        else:
            self.off()