import time
import RPi.GPIO as GPIO

#treba u setings dodati dva pina
class UltrasonicSensor:
    def __init__(self, trig_pin=4, echo_pin=17):
        GPIO.setmode(GPIO.BCM)

        self.trig = trig_pin
        self.echo = echo_pin

        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)

        GPIO.output(self.trig, False)
        time.sleep(0.5)  # stabilizacija senzora

    def read_distance(self):
        GPIO.output(self.trig, True)
        time.sleep(0.00001)
        GPIO.output(self.trig, False)

        start_time = time.time()
        while GPIO.input(self.echo) == 0:
            start_time = time.time()

        stop_time = time.time()
        while GPIO.input(self.echo) == 1:
            stop_time = time.time()

        time_elapsed = stop_time - start_time
        distance = (time_elapsed * 34300) / 2

        return round(distance, 2)  

def run_ultrasonic_loop(sensor, delay, callback, stop_event):
    while True:
        distance = sensor.read_distance()
        callback(distance)

        time.sleep(delay)
        if stop_event.is_set():
            break