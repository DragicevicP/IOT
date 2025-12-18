import time
import threading

def _ts():
    return time.strftime("%H:%M:%S")

def run_door_buzzer(settings, registry: dict, stop_event):
    """
    registry: dict u koji upisujemo instancu pod ključem 'DB'
    """
    if settings.get("simulated", True):
        from simulators.door_buzzer import SimDoorBuzzer
        buzzer = SimDoorBuzzer()
        print(f"[{_ts()}] DB ready (sim)")
    else:
        from sensors.door_buzzer import DoorBuzzer
        pin = settings["pin"]
        active_high = settings.get("active_high", True)
        buzzer = DoorBuzzer(pin, active_high=active_high)
        print(f"[{_ts()}] DB ready (GPIO pin={pin})")

    registry["DB"] = buzzer

def handle_db_command(cmd, registry: dict, stop_event):
    """
    Komande:
      db on
      db off
      db beep
      db beep <count>
      db beep <count> <on_ms> <off_ms>
      help
      exit
    """
    print("CLI ready. Type: help")

    while not stop_event.is_set():
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            stop_event.set()
            break

        if not line:
            continue

        cmd = line.lower().split()

        if cmd[0] in ("exit", "quit"):
            stop_event.set()
            break

        if cmd[0] == "help":
            print("Commands:")
            print("  db on")
            print("  db off")
            print("  db beep")
            print("  db beep <count>")
            print("  db beep <count> <on_ms> <off_ms>")
            print("  exit")
            continue

        if cmd[0] != "db":
            print("Unknown command. Type: help")
            continue

        buzzer = registry.get("DB")
        if buzzer is None:
            print("DB not configured/started.")
            continue

        if len(cmd) == 1:
            print("Usage: db on|off|beep ...")
            continue

        action = cmd[1]

        if action == "on":
            buzzer.on()
            print(f"[{_ts()}] DB: ON")
        elif action == "off":
            buzzer.off()
            print(f"[{_ts()}] DB: OFF")
        elif action == "beep":
            count = int(cmd[2]) if len(cmd) >= 3 else 1
            on_ms = int(cmd[3]) if len(cmd) >= 4 else 200
            off_ms = int(cmd[4]) if len(cmd) >= 5 else 200
            # beep u thread-u da ne blokira CLI
            t = threading.Thread(target=buzzer.beep, args=(count, on_ms, off_ms, stop_event), daemon=True)
            t.start()
            print(f"[{_ts()}] DB: BEEP x{count}")
        else:
            print("Unknown db action. Use: on/off/beep")
