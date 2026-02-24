# simulators/brgb.py
import time

class SimBedroomRGB:
    def __init__(self):
        self.current = (0, 0, 0)

    def _log(self, msg: str):
        t = time.strftime("%H:%M:%S")
        print(f"[{t}] BRGB (sim): {msg}")

    def set_rgb(self, r: int, g: int, b: int):
        self.current = (int(bool(r)), int(bool(g)), int(bool(b)))
        self._log(f"set_rgb={self.current}")

    def off(self):
        self.set_rgb(0, 0, 0)

    def white(self):      self.set_rgb(1, 1, 1)
    def red(self):        self.set_rgb(1, 0, 0)
    def green(self):      self.set_rgb(0, 1, 0)
    def blue(self):       self.set_rgb(0, 0, 1)
    def yellow(self):     self.set_rgb(1, 1, 0)
    def purple(self):     self.set_rgb(1, 0, 1)

    def set_color_name(self, name: str):
        name = (name or "").strip().lower()
        mapping = {
            "off": self.off,
            "white": self.white,
            "red": self.red,
            "green": self.green,
            "blue": self.blue,
            "yellow": self.yellow,
            "purple": self.purple
        }
        (mapping.get(name) or self.off)()