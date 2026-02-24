# sensors/dht11_sensor.py
import time
import RPi.GPIO as GPIO


class DHTSensor:
    DHTLIB_OK = 0
    DHTLIB_ERROR_CHECKSUM = -1
    DHTLIB_ERROR_TIMEOUT = -2
    DHTLIB_INVALID_VALUE = -999

    DHTLIB_DHT11_WAKEUP = 0.020  # 20ms
    DHTLIB_TIMEOUT = 0.0001      # 100us

    def __init__(self, pin):
        self.pin = pin
        self.bits = [0, 0, 0, 0, 0]
        self.humidity = self.DHTLIB_INVALID_VALUE
        self.temperature = self.DHTLIB_INVALID_VALUE

    def _read_sensor(self, wakeup_delay):
        mask = 0x80
        idx = 0
        self.bits = [0, 0, 0, 0, 0]

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        time.sleep(wakeup_delay)
        GPIO.output(self.pin, GPIO.HIGH)
        GPIO.setup(self.pin, GPIO.IN)

        loop_cnt = self.DHTLIB_TIMEOUT

        t = time.time()
        while GPIO.input(self.pin) == GPIO.LOW:
            if (time.time() - t) > loop_cnt:
                return self.DHTLIB_ERROR_TIMEOUT

        t = time.time()
        while GPIO.input(self.pin) == GPIO.HIGH:
            if (time.time() - t) > loop_cnt:
                return self.DHTLIB_ERROR_TIMEOUT

        for _ in range(40):
            t = time.time()
            while GPIO.input(self.pin) == GPIO.LOW:
                if (time.time() - t) > loop_cnt:
                    return self.DHTLIB_ERROR_TIMEOUT

            t = time.time()
            while GPIO.input(self.pin) == GPIO.HIGH:
                if (time.time() - t) > loop_cnt:
                    return self.DHTLIB_ERROR_TIMEOUT

            if (time.time() - t) > 0.00005:
                self.bits[idx] |= mask

            mask >>= 1
            if mask == 0:
                mask = 0x80
                idx += 1

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.HIGH)
        return self.DHTLIB_OK

    def read(self):
        rv = self._read_sensor(self.DHTLIB_DHT11_WAKEUP)
        if rv != self.DHTLIB_OK:
            self.humidity = self.DHTLIB_INVALID_VALUE
            self.temperature = self.DHTLIB_INVALID_VALUE
            return {
                "ok": False,
                "code": rv,
                "humidity": self.humidity,
                "temperature": self.temperature,
            }

        humidity = self.bits[0]
        temperature = self.bits[2] + self.bits[3] * 0.1
        sum_chk = (self.bits[0] + self.bits[1] + self.bits[2] + self.bits[3]) & 0xFF
        if self.bits[4] != sum_chk:
            self.humidity = self.DHTLIB_INVALID_VALUE
            self.temperature = self.DHTLIB_INVALID_VALUE
            return {
                "ok": False,
                "code": self.DHTLIB_ERROR_CHECKSUM,
                "humidity": self.humidity,
                "temperature": self.temperature,
            }

        self.humidity = humidity
        self.temperature = temperature
        return {
            "ok": True,
            "code": self.DHTLIB_OK,
            "humidity": self.humidity,
            "temperature": self.temperature,
        }


def run_dht_loop(sensor: DHTSensor, delay, callback, stop_event):
    while not stop_event.is_set():
        data = sensor.read()
        callback(data)
        time.sleep(delay)