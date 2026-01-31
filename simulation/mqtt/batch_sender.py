import time
from queue import Queue, Empty


class MQTTSenderDaemon:
    def __init__(self, mqtt_client, batch_size=10, flush_interval=2.0):
        self.queue = Queue()
        self.client = mqtt_client
        self.batch_size = batch_size
        self.flush_interval = flush_interval

    def put(self, topic, payload):
        self.queue.put((topic, payload))

    def run(self, stop_event):
        batch = []
        last_flush = time.time()

        while not stop_event.is_set():
            try:
                item = self.queue.get(timeout=0.2)
                batch.append(item)
            except Empty:
                pass

            now = time.time()

            if (len(batch) >= self.batch_size
                or (batch and now - last_flush >= self.flush_interval)):
                
                self.client.publish_batch(batch)
                batch.clear()
                last_flush = now
