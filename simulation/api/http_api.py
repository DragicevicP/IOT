import threading
from flask import Flask, request, jsonify

def start_http_api(settings, registry, event_bus, stop_event, host="0.0.0.0", port=5001):
    app = Flask(__name__)

    @app.after_request
    def add_cors_headers(resp):
        resp.headers["Access-Control-Allow-Origin"] = "http://localhost:4200"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"ok": True})
    
    @app.route("/api/alarm/state", methods=["GET"])
    def alarm_state():
        return jsonify({"alarm_on": bool(registry.get("_alarm_on", False))})
    
    @app.route("/api/4sd/set", methods=["POST", "OPTIONS"])
    def four_sd_set():
        if request.method == "OPTIONS":
            return ("", 204)

        data = request.get_json(silent=True) or {}
        value = str(data.get("value", "")).strip()

        value = value.replace(":", "")
        if len(value) != 4 or not value.isdigit():
            return jsonify({"ok": False, "error": "invalid_value", "hint": "Use HH:MM or HHMM"}), 400

        from components.kitchen_segment_display import handle_4sd_command
        handle_4sd_command(["4sd", value], registry, stop_event)
        return jsonify({"ok": True, "value": value})


    @app.route("/api/4sd/time", methods=["POST", "OPTIONS"])
    def four_sd_time():
        if request.method == "OPTIONS":
            return ("", 204)

        from components.kitchen_segment_display import handle_4sd_command
        handle_4sd_command(["4sd", "time"], registry, stop_event)
        return jsonify({"ok": True})

    @app.route("/api/dms/pin", methods=["POST", "OPTIONS"])
    def dms_pin():
        if request.method == "OPTIONS":
            return ("", 204)

        data = request.get_json(silent=True) or {}
        pin = str(data.get("pin", "")).strip()
        if pin.endswith("#"):
            pin = pin[:-1]

        dms_cfg = (settings.get("devices", {}).get("DMS", {}) or {})
        expected = str(dms_cfg.get("pin_code", "1234")).strip()
        ok = (pin == expected)

        if ok and event_bus is not None:
            from logic.events import PinEvent, now_ts
            event_bus.publish(PinEvent(source_id="DMS", pin=pin, timestamp=now_ts()))

        mqtt_sender = registry.get("_mqtt_sender")
        system_info = registry.get("_system")
        if mqtt_sender and system_info:
            from mqtt.topics import sensor_topic
            from mqtt.payload import build_payload
            status = "PIN_OK" if ok else "PIN_BAD"
            mqtt_sender.put(
                sensor_topic(system_info["pi"], "DMS"),
                build_payload(system_info, "DMS", status, True)
            )

        return jsonify({"ok": True, "pin_ok": ok})

    @app.route("/api/brgb/color", methods=["POST", "OPTIONS"])
    def brgb_color():
        if request.method == "OPTIONS":
            return ("", 204)

        data = request.get_json(silent=True) or {}
        color = str(data.get("color", "")).strip().lower()

        allowed = {"red", "green", "blue", "yellow", "purple", "white", "off"}
        if color not in allowed:
            return jsonify({"ok": False, "error": "invalid_color", "allowed": sorted(list(allowed))}), 400

        from components.bedroom_rgb import handle_brgb_command
        if color == "off":
            handle_brgb_command(["brgb", "off"], registry, stop_event)
        else:
            handle_brgb_command(["brgb", color], registry, stop_event)

        return jsonify({"ok": True})

    print(f"[API] Running on http://localhost:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)