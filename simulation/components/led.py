import time

def _ts():
    return time.strftime("%H:%M:%S")

def run_door_ligth(settings, registry: dict, stop_event):

    if settings.get("simulated", True):
        from simulators.led import led_on as sim_led_on, led_off as sim_led_off
        print(f"[{_ts()}] DL ready (sim)")
        registry["DL_on"] = sim_led_on
        registry["DL_off"] = sim_led_off
    else:
        from sensors.led import Led
        led = Led(settings["pin"])
        print(f"[{_ts()}] DL ready (GPIO pin={settings['pin']})")
        registry["DL_on"] = led.on
        registry["DL_off"] = led.off


def handle_dl_command(cmd, registry, stop_event):
    light = registry.get("DL")
    if not light:
        print("DL not configured.")
        return

    if len(cmd) < 2:
        print("Usage: dl on | dl off")
        return

    action = cmd[1]

    if action == "on":
        light.on()
        print("DL: ON")

    elif action == "off":
        light.off()
        print("DL: OFF")

    else:
        print("Unknown DL command. Use: dl on | dl off")
