import json

def load_settings(filePath='settings.json'):
    with open(filePath, 'r') as f:
        return json.load(f)
    
def get_device_settings(settings, device_name):
    return settings["devices"][device_name]

def is_simulated(device_settings):
    if "simulated" not in device_settings:
        raise KeyError("Missing 'simulated' field in device settings")

    return device_settings["simulated"]