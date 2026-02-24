import RPi.GPIO as GPIO
import time
class DoorMembraneSwitchKeypad:
    """
    4x4 keypad: skenira rows/cols.
    Default layout:
    1 2 3 A
    4 5 6 B
    7 8 9 C
    * 0 # D
    """
    DEFAULT_KEYS = [
        ['1', '2', '3', 'A'],
        ['4', '5', '6', 'B'],
        ['7', '8', '9', 'C'],
        ['*', '0', '#', 'D'],
    ]

    def __init__(self, rows, cols, keys=None, debounce_ms=150):
        GPIO.setmode(GPIO.BCM)

        self.rows = list(rows)
        self.cols = list(cols)
        self.keys = keys if keys is not None else self.DEFAULT_KEYS

        self.debounce_ms = debounce_ms
        self._last_key = None
        self._last_key_ts = 0

        for r in self.rows:
            GPIO.setup(r, GPIO.OUT)
            GPIO.output(r, GPIO.HIGH)

        for c in self.cols:
            GPIO.setup(c, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read_key(self):
        now_ms = int(time.time() * 1000)

        for r_i, r_pin in enumerate(self.rows):
            GPIO.output(r_pin, GPIO.LOW)

            for c_i, c_pin in enumerate(self.cols):
                if GPIO.input(c_pin) == GPIO.LOW:
                    key = self.keys[r_i][c_i]
                    GPIO.output(r_pin, GPIO.HIGH)

                    if self._last_key == key and (now_ms - self._last_key_ts) < self.debounce_ms:
                        return None

                    self._last_key = key
                    self._last_key_ts = now_ms

                
                    while GPIO.input(c_pin) == GPIO.LOW:
                        time.sleep(0.01)

                    return key

            GPIO.output(r_pin, GPIO.HIGH)

        return None


def run_dms_loop(keypad: DoorMembraneSwitchKeypad, delay: float, callback, stop_event):
    while True:
        key = keypad.read_key()
        if key is not None:
            callback(key)

        time.sleep(delay)
        if stop_event.is_set():
            break