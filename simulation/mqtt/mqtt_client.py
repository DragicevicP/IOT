import json
import paho.mqtt.client as mqtt


class MQTTClient:
    def __init__(self, host="localhost", port=1883):
        self.client = mqtt.Client()
        self.client.connect(host, port)
        self.client.loop_start()

    def publish_batch(self, messages: list):
        for topic, payload in messages:
            self.client.publish(topic, json.dumps(payload))
