import time

def build_payload( system_info: dict, device_id: str, value, simulated: bool):
    return {
        "pi_id": system_info["pi_id"],
        "system": system_info["device_name"],
        "location": system_info["location"],
        "device_id": device_id,
        "value": value,
        "simulated": simulated,
        "timestamp": int(time.time())
    }