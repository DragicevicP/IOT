from components.door_buzzer import handle_db_command
from components.led import handle_dl_command
from simulators.door_membrane_switch import push_dms_sequence
from components.bedroom_rgb import handle_brgb_command

def cli_loop(registry, stop_event):
    while not stop_event.is_set():
        line = input("> ").strip().lower()
        if not line:
            continue

        cmd = line.split()
        op = cmd[0].lower()

        if op == "exit":
            stop_event.set()
            break

        elif op == "db":
            handle_db_command(cmd, registry, stop_event)

        elif op == "dl":
            handle_dl_command(cmd, registry, stop_event)

        elif op == "dms":
            if len(cmd) < 2:
                print("Usage: dms <sequence> (e.g. dms 1234# or dms 12*)")
                continue
            seq = "".join(cmd[1:])  
            push_dms_sequence(seq)
        elif op == "brgb":
            if len(cmd) < 2:
                print("Usage: brgb <color|off|on> [color]  OR  brgb rgb <r> <g> <b>")
                continue

            if cmd[1] == "rgb":
                if len(cmd) != 5:
                    print("Usage: brgb rgb <r> <g> <b>  (values: 0/1)")
                    continue
                try:
                    r = int(cmd[2]); g = int(cmd[3]); b = int(cmd[4])
                except ValueError:
                    print("RGB values must be integers 0 or 1.")
                    continue

                handle_brgb_command({"rgb": [r, g, b]}, registry)
                continue
            if cmd[1] == "off":
                handle_brgb_command("off", registry)
                continue
            if cmd[1] == "on":
                color = cmd[2] if len(cmd) >= 3 else "white"
                handle_brgb_command({"on": True, "color": color}, registry)
                continue
            handle_brgb_command(cmd, registry, stop_event)

        else:
            print("Unknown command")