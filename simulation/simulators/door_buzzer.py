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


