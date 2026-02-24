import json
import threading

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from flask import Flask, request, jsonify


MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "smart_home/#"

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "super-secret-token"
INFLUX_ORG = "iot"
INFLUX_BUCKET = "smart_home"
influx = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

write_api = influx.write_api()
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC)
    print(f"[MQTT] Subscribed to {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return

    try:
        point = (
            Point("telemetry")
            .tag("pi_id", payload["pi_id"])
            .tag("device_id", payload["device_id"])
            .tag("location", payload["location"])
            .field("value", str(payload["value"]))
            .field("simulated", bool(payload["simulated"]))
            .time(payload["timestamp"], WritePrecision.S)
        )

        write_api.write(bucket=INFLUX_BUCKET, record=point)

        print(f"[INFLUX] {payload['device_id']} -> {payload['value']}")

    except KeyError:
        pass

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
    mqtt_client.loop_forever()

#TODO:
# -------- Flask (aktuatore kasnije) --------
app = Flask(__name__)

@app.post("/actuate")
def actuate():
    data = request.json
    topic = f"smart_home/{data['pi_id']}/{data['device_id']}/cmd"
    mqtt_client.publish(topic, json.dumps(data))
    return jsonify({"ok": True})

if __name__ == "__main__":
    t = threading.Thread(target=start_mqtt, daemon=True)
    t.start()

    print("[SERVER] Running on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000)
