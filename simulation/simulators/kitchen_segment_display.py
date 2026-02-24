def run_display_simulator(display, stop_event):
    print("[SIM DISPLAY] Started")
    while not stop_event.is_set():
        pass

class SimulatedDisplay:
    def set_value(self, text):
        print(f"[SIM DISPLAY] {text}")