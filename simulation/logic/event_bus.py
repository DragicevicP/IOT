import queue
from typing import Optional
from logic.events import DeviceEvent

class EventBus:
    def __init__(self, maxsize: int = 1000):
        self._q: queue.Queue[DeviceEvent] = queue.Queue(maxsize=maxsize)

    def publish(self, event: DeviceEvent) -> None:
        try:
            self._q.put_nowait(event)
        except queue.Full:
            pass

    def get(self, timeout: Optional[float] = None) -> DeviceEvent:
        return self._q.get(timeout=timeout)