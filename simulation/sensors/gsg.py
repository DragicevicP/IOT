import time
import math

from sensors.MPU6050.MPU6050 import MPU6050

class GSGSensor:
    def __init__(self, threshold_g: float = 0.35):
        self.mpu = MPU6050()
        self.mpu.dmp_initialize()
        self.threshold_g = float(threshold_g)

    def read(self) -> int:
        ax, ay, az = self.mpu.get_acceleration()
        axg, ayg, azg = ax/16384.0, ay/16384.0, az/16384.0

        mag = math.sqrt(axg*axg + ayg*ayg + azg*azg)
        delta = abs(mag - 1.0)

        return 1 if delta >= self.threshold_g else 0


def run_gsg_loop(sensor: GSGSensor, delay, callback, stop_event):
    while not stop_event.is_set():
        callback(sensor.read())
        time.sleep(delay)