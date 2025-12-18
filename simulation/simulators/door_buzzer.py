import time

class SimDoorBuzzer:
    def __init__(self):
        self.state = False

    def on(self):
        self.state = True
        print("DB (sim): ON")

    def off(self):
        self.state = False
        print("DB (sim): OFF")

    def beep(self, count: int = 1, on_ms: int = 200, off_ms: int = 200, stop_event=None):
        for i in range(max(0, int(count))):
            if stop_event is not None and stop_event.is_set():
                break
            print(f"DB (sim): BEEP {i+1}/{count} (on={on_ms}ms off={off_ms}ms)")
            time.sleep((max(0, on_ms) + max(0, off_ms)) / 1000.0)
