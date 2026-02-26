# logic/engine.py
import time
from typing import Dict, Optional, Deque, Tuple
from logic.event_bus import EventBus
from logic.events import DeviceEvent
from components.led import publish_dl_state
from mqtt.topics import sensor_topic
from mqtt.payload import build_payload
from logic.events import DeviceEvent, PinEvent
import queue
from collections import deque


class LogicEngine:
    def __init__(self, settings: dict, registry: dict, bus: EventBus):
        self.settings = settings
        self.registry = registry
        self.bus = bus
        logic_cfg = settings.get("logic", {})

        self.motion_light_rules: Dict[str, dict] = logic_cfg.get("motion_light", {})
        self._last_motion_state_light: Dict[str, int] = {}
        self._light_off_at: Dict[str, float] = {}
        self.door_unlock_rules = (
            settings.get("logic", {})
                    .get("door_unlock_alarm", {})
        )
        self._door_open_since = {}    # device_id -> timestamp
        self._alarm_on = False
        self.alarm_pin = str(settings["devices"]["DMS"]["pin_code"])


        people_cfg = logic_cfg.get("people_counter", {})
        self.people_pairs: Dict[str, dict] = people_cfg.get("pairs", {})
        self.window_sec = float(people_cfg.get("window_sec", 4))
        self.min_samples = int(people_cfg.get("min_samples", 4))
        self.delta_threshold = float(people_cfg.get("delta_cm_threshold", 20))
        self.cooldown_sec = float(people_cfg.get("cooldown_sec", 3))
        self.publish_device_id = people_cfg.get("publish_device_id", "PEOPLE_COUNT")

        self.persons_count = 0
        self._last_motion_state_people: Dict[str, int] = {}
        self._last_count_ts: Dict[str, float] = {}
        self._dus_history: Dict[str, Deque[Tuple[float, float]]] = {}
        self._dus_maxlen = 200

        self._debug_people_delta = bool(people_cfg.get("debug", False))

        self._alarm_on = False
        alarm_cfg = logic_cfg.get("alarm_when_empty", {})
        self.alarm_pirs = set(alarm_cfg.get("pir_ids", ["DPIR1", "DPIR2", "DPIR3"]))
        self._last_motion_state_alarm: Dict[str, int] = {}

        lcd_cfg = logic_cfg.get("lcd_rotate_dht", {})
        self.lcd_rotate_enabled = bool(lcd_cfg.get("enabled", False))
        self.lcd_id = lcd_cfg.get("lcd_id", "LCD")
        self.lcd_dht_ids = list(lcd_cfg.get("dht_ids", ["DHT1", "DHT2", "DHT3"]))
        self.lcd_interval_sec = float(lcd_cfg.get("interval_sec", 3))

        self._lcd_next_at = time.time() + self.lcd_interval_sec
        self._lcd_idx = 0
        self._last_dht_data = {} 

        self._armed = False
        self._arming_until = 0.0
        self._entry_until = 0.0
        self._waiting_entry_pin = False

        # --- SECURITY CONFIG ---
        sec_cfg = logic_cfg.get("security", {})

        self.security_enabled = bool(sec_cfg)
        self.security_keypad_id = sec_cfg.get("keypad_id", "DMS")
        self.security_doors = set(sec_cfg.get("door_ids", ["DS1", "DS2"]))
        self.security_buzzer_id = sec_cfg.get("buzzer_id", "DB")
        self.arm_delay_sec = float(sec_cfg.get("arm_delay_sec", 10))
        self.entry_delay_sec = float(sec_cfg.get("entry_delay_sec", 0))

    def _truthy_motion(self, value) -> int:
        return 1 if bool(value) else 0

    def _turn_light_on(self, light_id: str):
        light = self.registry.get(light_id)
        if not light:
            print(f"[LOGIC] Light '{light_id}' not found in registry")
            return
        light.on()
        if light_id == "DL":
            publish_dl_state(self.registry, 1)

    def _turn_light_off(self, light_id: str):
        light = self.registry.get(light_id)
        if not light:
            return
        light.off()
        if light_id == "DL":
            publish_dl_state(self.registry, 0)

    def _publish_people_count(self, system_info: dict, simulated: bool):
        mqtt_sender = self.registry.get("_mqtt_sender")
        if not mqtt_sender:
            return
        topic = sensor_topic(system_info["pi"], self.publish_device_id)
        payload = build_payload(system_info, self.publish_device_id, self.persons_count, simulated)
        mqtt_sender.put(topic, payload)
    
    def _save_alarm_state(self, is_on: bool):
        sender = self.registry.get("_mqtt_sender")
        sys_info = self.registry.get("_system")
        if not sender or not sys_info:
            return

        sender.put(
            sensor_topic(sys_info["pi"], "ALARM"),
            build_payload(sys_info, "ALARM", bool(is_on), True)
        )

    def _store_dus(self, dus_id: str, distance: float):
        now = time.time()
        dq = self._dus_history.get(dus_id)
        if dq is None:
            dq = deque(maxlen=self._dus_maxlen)
            self._dus_history[dus_id] = dq

        dq.append((now, float(distance)))
        while dq and (now - dq[0][0] > self.window_sec):
            dq.popleft()

    def _handle_motion_light(self, ev: DeviceEvent):
        rule = self.motion_light_rules.get(ev.device_id)
        if not rule:
            return

        motion = self._truthy_motion(ev.value)
        prev = self._last_motion_state_light.get(ev.device_id, 0)
        self._last_motion_state_light[ev.device_id] = motion

        if prev == 0 and motion == 1:
            light_id = rule.get("light_id", "DL")
            duration = float(rule.get("duration_sec", 10))

            print(f"[LOGIC] {ev.device_id} motion -> {light_id} ON for {duration}s")
            self._turn_light_on(light_id)
            self._light_off_at[light_id] = time.time() + duration

    def _handle_people_counter(self, ev: DeviceEvent):
       
        if ev.device_id.startswith("DUS"):
            self._store_dus(ev.device_id, ev.value)
            return

        cfg = self.people_pairs.get(ev.device_id)
        if not cfg:
            return

        motion = self._truthy_motion(ev.value)
        prev = self._last_motion_state_people.get(ev.device_id, 0)
        self._last_motion_state_people[ev.device_id] = motion

        if not (prev == 0 and motion == 1):
            return

        now = time.time()
        last_ts = self._last_count_ts.get(ev.device_id, 0.0)
        if now - last_ts < self.cooldown_sec:
            return

        dus_id = cfg["dus_id"]
        approach_means = cfg.get("approach_means", "ENTER") 

        hist = list(self._dus_history.get(dus_id, []))
        if len(hist) < self.min_samples:
            print(f"[PEOPLE] {ev.device_id}: not enough {dus_id} samples ({len(hist)}/{self.min_samples})")
            return

        distances = [d for _, d in hist]
        mid = len(distances) // 2
        before = distances[:mid]
        after = distances[mid:]

        if not before or not after:
            return

        avg_before = sum(before) / len(before)
        avg_after = sum(after) / len(after)
        delta = avg_after - avg_before

        if self._debug_people_delta:
            print(f"[PEOPLE-DBG] {ev.device_id}/{dus_id} before={avg_before:.1f} after={avg_after:.1f} delta={delta:.1f}")

        if delta < -self.delta_threshold:
            direction = "APPROACH"
        elif delta > self.delta_threshold:
            direction = "LEAVE"
        else:
            return

        if direction == "APPROACH":
            action = approach_means
        else:
            action = "EXIT" if approach_means == "ENTER" else "ENTER"

        old = self.persons_count
        if action == "ENTER":
            self.persons_count += 1
        else:
            self.persons_count = max(0, self.persons_count - 1)

        if self.persons_count != old:
            self._last_count_ts[ev.device_id] = now
            print(f"[PEOPLE] {action} -> persons {old} -> {self.persons_count}")
            self._publish_people_count(ev.system_info, ev.simulated)
    
    def _handle_alarm_when_empty(self, ev: DeviceEvent):
        if ev.device_id not in self.alarm_pirs:
            return

        motion = self._truthy_motion(ev.value)
        prev = self._last_motion_state_alarm.get(ev.device_id, 0)
        self._last_motion_state_alarm[ev.device_id] = motion

        if not (prev == 0 and motion == 1):
            return

        if self.persons_count != 0:
            return

        if not self._alarm_on:
            self._alarm_on = True
            print(f"[ALARM] ON (empty + motion on {ev.device_id})")
            self._save_alarm_state(True)

    def _process_scheduled(self):
        now = time.time()

        # ARMING -> ARMED posle 10s
        if self.security_enabled and (not self._armed) and self._arming_until and now >= self._arming_until:
            self._arming_until = 0.0
            self._armed = True
            self.registry["_system_on"] = bool(self._armed)
            print("[SEC] ARMED")

        # ENTRY window istekao -> ALARM ON
        # if self.security_enabled and self._armed and self._waiting_entry_pin and (not self._alarm_on) and now >= self._entry_until:
        #     self._waiting_entry_pin = False
        #     self._alarm_on = True
        #     print("[SEC] ALARM ON (entry timeout)")
        #     self._set_buzzer(self.security_buzzer_id, True)
        #     self._save_alarm_state(True)

        to_off = [lid for lid, ts in self._light_off_at.items() if ts <= now]
        for lid in to_off:
            print(f"[LOGIC] {lid} OFF (timer)")
            self._turn_light_off(lid)
            del self._light_off_at[lid]
        
        if self.lcd_rotate_enabled and time.time() >= self._lcd_next_at:
            self._lcd_next_at = time.time() + self.lcd_interval_sec

            lcd = self.registry.get(self.lcd_id)
            if not lcd:
                return

            dht_id = self.lcd_dht_ids[self._lcd_idx % len(self.lcd_dht_ids)]
            self._lcd_idx += 1

            data = self._last_dht_data.get(dht_id)
            if not data or not data.get("ok"):
                line1 = f"{dht_id}"
                line2 = "NO DATA/ERR"
            else:
                t = data.get("temperature")
                h = data.get("humidity")
                line1 = f"{dht_id}  T:{t}C"
                line2 = f"H:{h}%"

            try:
                lcd.write_lines(line1, line2)
            except Exception as e:
                print(f"[LCD] write failed: {e}")
                return

            sender = self.registry.get("_mqtt_sender")
            sys_info = self.registry.get("_system")
            if sender and sys_info:
                sender.put(
                    sensor_topic(sys_info["pi"], self.lcd_id),
                    build_payload(sys_info, self.lcd_id, f"{line1} | {line2}", True)
                )


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

            if self.lcd_rotate_enabled:
                self._handle_dht_for_lcd(ev)
            
            self._handle_motion_light(ev)
            self._handle_door_unlock_alarm(ev)

            self._handle_alarm_when_empty(ev)
            self._handle_people_counter(ev)
            self._handle_gsg_alarm(ev)
            self._handle_security_doors(ev)

    def _save_alarm_state(self, is_on: bool):
        sender = self.registry.get("_mqtt_sender")
        sys_info = self.registry.get("_system")
        if not sender or not sys_info:
            return

        sender.put(
            sensor_topic(sys_info["pi"], "ALARM"),
            build_payload(sys_info, "ALARM", bool(is_on), True)
        )
        self.registry["_alarm_on"] = bool(is_on)

    def _set_buzzer(self, buzzer_id: str, on: bool):
        buzzer = self.registry.get(buzzer_id)

        # LOCAL buzzer (isti PI)
        if buzzer:
            try:
                buzzer.on() if on else buzzer.off()
                return
            except Exception as e:
                print(f"[LOGIC] Failed to set local buzzer {buzzer_id}: {e}")
                return

        # REMOTE buzzer (drugi PI preko MQTT)
        sender = self.registry.get("_mqtt_sender")
        sys_info = self.registry.get("_system")

        if not sender or not sys_info:
            print("[LOGIC] MQTT sender missing")
            return

        # BUZZER JE NA PI1 — hardcoded ili iz settings
        target_pi = "PI1"

        payload = {
            "pi_id": target_pi,
            "device_id": buzzer_id,
            "command": "ON" if on else "OFF"
        }

        topic = f"smart_home/{target_pi}/{buzzer_id}/cmd"
        sender.put(topic, payload)

        print(f"[LOGIC] Remote buzzer {buzzer_id} -> {payload['command']} ({target_pi})")

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

        now = time.time()

        if self._alarm_on:
            print("[LOGIC] PIN OK -> ALARM OFF + DISARM")
            self._alarm_on = False
            self._armed = False
            self.registry["_system_on"] = bool(self._armed)
            self._arming_until = 0.0
            self._door_open_since.clear()
            self._set_buzzer("DB", False)
            self._save_alarm_state(False)
            return

        if self._armed:
            print("[LOGIC] PIN OK -> DISARM")
            self._armed = False
            self.registry["_system_on"] = bool(self._armed)
            self._arming_until = 0.0
            return

        if self._arming_until:
            print("[LOGIC] ARMING canceled")
            self._arming_until = 0.0
            return

        self._arming_until = now + 10
        print("[LOGIC] ARMING... system will activate in 10s")

    def _handle_dht_for_lcd(self, ev: DeviceEvent):
        if ev.device_id not in self.lcd_dht_ids:
            return
        if isinstance(ev.value, dict):
            self._last_dht_data[ev.device_id] = ev.value

    def _handle_gsg_alarm(self, ev: DeviceEvent):
        if ev.device_id != "GSG":
            return
        if int(bool(ev.value)) == 1 and not self._alarm_on:
            print("[LOGIC] ALARM ON: GSG significant movement")
            self._alarm_on = True
            self._set_buzzer("DB", True)
            self._save_alarm_state(True)

    def _disarm_all(self, reason: str):
        if self._alarm_on:
            print(f"[SEC] DISARM ({reason}) -> ALARM OFF")
        else:
            print(f"[SEC] DISARM ({reason})")

        self._alarm_on = False
        self._armed = False
        self.registry["_system_on"] = bool(self._armed)
        self._arming_until = 0.0
        self._entry_until = 0.0
        self._waiting_entry_pin = False

        self._set_buzzer(self.security_buzzer_id, False)
        self._save_alarm_state(False)

    def _handle_security_doors(self, ev: DeviceEvent):
        if not self.security_enabled:
            return
        if ev.device_id not in self.security_doors:
            return
        if not self._armed:
            return
        if self._alarm_on:
            return

        is_open = 1 if bool(ev.value) else 0

        if is_open:
            print(f"[SEC] ALARM ON (door breach: {ev.device_id})")
            self._alarm_on = True
            self._set_buzzer(self.security_buzzer_id, True)
            self._save_alarm_state(True)