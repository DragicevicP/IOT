import RPi.GPIO as GPIO
import time
import threading

class FourDigitDisplay:

    num = {
        ' ':(0,0,0,0,0,0,0),
        '0':(1,1,1,1,1,1,0),
        '1':(0,1,1,0,0,0,0),
        '2':(1,1,0,1,1,0,1),
        '3':(1,1,1,1,0,0,1),
        '4':(0,1,1,0,0,1,1),
        '5':(1,0,1,1,0,1,1),
        '6':(1,0,1,1,1,1,1),
        '7':(1,1,1,0,0,0,0),
        '8':(1,1,1,1,1,1,1),
        '9':(1,1,1,1,0,1,1)
    }

    def __init__(self, segments, digits):
        self.segments = segments
        self.digits = digits
        self.value = "    "
        self.running = True

        for seg in segments:
            GPIO.setup(seg, GPIO.OUT)
            GPIO.output(seg, 0)

        for dig in digits:
            GPIO.setup(dig, GPIO.OUT)
            GPIO.output(dig, 1)

        self.thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self.thread.start()

    def set_value(self, text):
        self.value = str(text).rjust(4)[:4]

    def _refresh_loop(self):
        while self.running:
            for d in range(4):
                char = self.value[d]
                pattern = self.num.get(char, self.num[' '])

                for i in range(7):
                    GPIO.output(self.segments[i], pattern[i])

                GPIO.output(self.digits[d], 0)
                time.sleep(0.001)
                GPIO.output(self.digits[d], 1)

    def stop(self):
        self.running = False