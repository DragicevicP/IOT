# logic/engine.py
import time
from typing import Dict, Optional
from logic.event_bus import EventBus
from logic.events import DeviceEvent
from components.led import publish_dl_state
from mqtt.topics import sensor_topic
from mqtt.payload import build_payload
from logic.events import DeviceEvent, PinEvent
import queue
class LogicEngine:
    def __init__(self, settings: dict, registry: dict, bus: EventBus):
        self.settings = settings
        self.registry = registry
        self.bus = bus

        self.motion_light_rules: Dict[str, dict] = (
            settings.get("logic", {})
                    .get("motion_light", {})
        )
        self._last_motion_state: Dict[str, int] = {}
        self._light_off_at: Dict[str, float] = {}
        self.door_unlock_rules = (
            settings.get("logic", {})
                    .get("door_unlock_alarm", {})
        )
        self._door_open_since = {}    # device_id -> timestamp
        self._alarm_on = False
        self.alarm_pin = str(settings["devices"]["DMS"]["pin_code"])


    def _truthy_motion(self, value) -> int:
        return 1 if bool(value) else 0

    def _turn_light_on(self, light_id: str):
        light = self.registry.get(light_id)
        if not light:
            print(f"[LOGIC] Light '{light_id}' not found in registry")
            return
        try:
            light.on()
            if light_id == "DL":
                publish_dl_state(self.registry, 1)
        except Exception as e:
            print(f"[LOGIC] Failed to turn ON {light_id}: {e}")

    def _turn_light_off(self, light_id: str):
        light = self.registry.get(light_id)
        if not light:
            return
        try:
            light.off()
            if light_id == "DL":
                publish_dl_state(self.registry, 0)
        except Exception as e:
            print(f"[LOGIC] Failed to turn OFF {light_id}: {e}")

    def _handle_motion_light(self, ev: DeviceEvent):
        rule = self.motion_light_rules.get(ev.device_id)
        if not rule:
            return

        motion = self._truthy_motion(ev.value)
        prev = self._last_motion_state.get(ev.device_id, 0)
        self._last_motion_state[ev.device_id] = motion
        if prev == 0 and motion == 1:
            light_id = rule.get("light_id", "DL")
            duration = float(rule.get("duration_sec", 10))

            print(f"[LOGIC] {ev.device_id} motion -> {light_id} ON for {duration}s")
            self._turn_light_on(light_id)
            self._light_off_at[light_id] = time.time() + duration

    def _process_scheduled(self):
        now = time.time()
        to_off = [lid for lid, ts in self._light_off_at.items() if ts <= now]
        for lid in to_off:
            print(f"[LOGIC] {lid} OFF (timer)")
            self._turn_light_off(lid)
            del self._light_off_at[lid]

    def run_loop(self, stop_event):
        while not stop_event.is_set():
            self._process_scheduled()
            
            try:
                ev = self.bus.get(timeout=0.2)
            except queue.Empty:
                continue


            if isinstance(ev, PinEvent):
                self._handle_pin_event(ev)
                continue

            
            self._handle_motion_light(ev)
            self._handle_door_unlock_alarm(ev)

    def _save_alarm_state(self, is_on: bool):
        sender = self.registry.get("_mqtt_sender")
        sys_info = self.registry.get("_system")
        if not sender or not sys_info:
            return

        sender.put(
            sensor_topic(sys_info["pi"], "ALARM"),
            build_payload(sys_info, "ALARM", bool(is_on), True)
        )

    def _set_buzzer(self, buzzer_id: str, on: bool):
        buzzer = self.registry.get(buzzer_id)
        if not buzzer:
            print(f"[LOGIC] Buzzer '{buzzer_id}' not found in registry")
            return
        try:
            if on:
                buzzer.on()
            else:
                buzzer.off()
        except Exception as e:
            print(f"[LOGIC] Failed to set buzzer {buzzer_id}={on}: {e}")

    def _handle_door_unlock_alarm(self, ev: DeviceEvent):
        rule = self.door_unlock_rules.get(ev.device_id)
        if not rule:
            return

        duration = float(rule.get("duration_sec", 5))
        buzzer_id = rule.get("buzzer_id", "DB")

        is_open = 1 if bool(ev.value) else 0
        now = time.time()

        if is_open:
            if ev.device_id not in self._door_open_since:
                self._door_open_since[ev.device_id] = now

            if not self._alarm_on and (now - self._door_open_since[ev.device_id]) >= duration:
                self._alarm_on = True
                print(f"[LOGIC] ALARM ON: {ev.device_id} open >= {duration}s")

                self._set_buzzer(buzzer_id, True)
                self._save_alarm_state(True)    
        else:
            if ev.device_id in self._door_open_since:
                del self._door_open_since[ev.device_id]

            if self._alarm_on:
                self._alarm_on = False
                print(f"[LOGIC] ALARM OFF: {ev.device_id} changed state")

                self._set_buzzer(buzzer_id, False)
                self._save_alarm_state(False)  
    
    def _handle_pin_event(self, ev: "PinEvent"):
        if ev.pin != self.alarm_pin:
            print("[LOGIC] Wrong PIN")
            return

        if self._alarm_on:
            print("[LOGIC] PIN OK -> ALARM OFF")
            self._alarm_on = False
            self._door_open_since.clear()
            self._set_buzzer("DB", False)
            self._save_alarm_state(False)