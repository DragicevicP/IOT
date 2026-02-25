# logic/engine.py
import time
from typing import Dict, Optional
from logic.event_bus import EventBus
from logic.events import DeviceEvent
from components.led import publish_dl_state

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
            except Exception:
                continue

            self._handle_motion_light(ev)