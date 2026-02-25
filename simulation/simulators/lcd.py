import time

def _ts():
    return time.strftime("%H:%M:%S")

class SimLCD:
    def __init__(self, cols=16, rows=2):
        self.cols = cols
        self.rows = rows
        self.last = ("", "")

    def clear(self):
        self.last = ("", "")

    def write_lines(self, line1: str, line2: str = ""):
        line1 = (line1 or "")[: self.cols]
        line2 = (line2 or "")[: self.cols]
        self.last = (line1, line2)
        print(f"[{_ts()}] [SIM] LCD:")
        print(f"  |{line1:<{self.cols}}|")
        if self.rows > 1:
            print(f"  |{line2:<{self.cols}}|")