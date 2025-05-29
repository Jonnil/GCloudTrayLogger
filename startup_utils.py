#!/usr/bin/env python3
"""
startup_utils.py

Enable or disable launching this script on system login across
Windows, macOS, and Linux (XDG Autostart).
"""
import os, sys, platform, subprocess

def enable_run_on_startup(enable: bool):
    system = platform.system()
    # our own script path + interpreter
    exe = sys.executable
    script = os.path.abspath(sys.argv[0])

    if system == "Windows":
        startup = os.path.join(
            os.getenv("APPDATA"),
            "Microsoft", "Windows",
            "Start Menu", "Programs", "Startup"
        )
        bat = os.path.join(startup, "GCloudTrayLogger_startup.bat")
        if enable:
            with open(bat, "w") as f:
                f.write(f'"{exe}" "{script}"\n')
        else:
            if os.path.exists(bat):
                os.remove(bat)

    elif system == "Darwin":
        name = os.path.basename(script)
        if enable:
            cmd = [
                "osascript", "-e",
                f'tell application "System Events" to make login item at end '
                f'with properties {{path:"{script}", hidden:false, name:"GCloud Tray Logger"}}'
            ]
        else:
            cmd = [
                "osascript", "-e",
                f'tell application "System Events" to delete login item "GCloud Tray Logger"'
            ]
        subprocess.call(cmd)

    else:
        # Linux / XDG autostart
        autostart = os.path.expanduser("~/.config/autostart")
        os.makedirs(autostart, exist_ok=True)
        desktop = os.path.join(autostart, "gcloudtraylogger.desktop")
        if enable:
            content = (
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=GCloud Tray Logger\n"
                f'Exec={exe} "{script}"\n'
                "X-GNOME-Autostart-enabled=true\n"
            )
            with open(desktop, "w") as f:
                f.write(content)
        else:
            if os.path.exists(desktop):
                os.remove(desktop)
