from queue import Queue, Empty
import time

DMS_QUEUE = Queue()

def push_dms_sequence(seq: str):
    DMS_QUEUE.put(seq)

def run_dms_simulator(delay, callback, stop_event):
    while not stop_event.is_set():
        try:
            seq = DMS_QUEUE.get(timeout=0.2) 
        except Empty:
            continue

        seq = (seq or "").strip()
        if not seq:
            continue

        for ch in seq:
            if stop_event.is_set():
                break
            callback(ch)
            time.sleep(delay)