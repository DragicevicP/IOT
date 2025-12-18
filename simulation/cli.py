from components.door_buzzer import handle_db_command
from components.led import handle_dl_command

def cli_loop(registry, stop_event):
    while not stop_event.is_set():
        line = input("> ").strip().lower()
        if not line:
            continue

        cmd = line.split()

        if cmd[0] == "exit":
            stop_event.set()
            break

        elif cmd[0] == "db":
            handle_db_command(cmd, registry, stop_event)

        elif cmd[0] == "dl":
            handle_dl_command(cmd, registry, stop_event)

        else:
            print("Unknown command")