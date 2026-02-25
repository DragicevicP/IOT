from dataclasses import dataclass
from typing import Any
import time

@dataclass(frozen=True)
class DeviceEvent:
    device_id: str
    value: Any
    simulated: bool
    timestamp: float
    system_info: dict

def now_ts() -> float:
    return time.time()