#!/usr/bin/env python3
"""
open_log_file.py

Helper to open the application's log file in the default system viewer,
and update the InfoBar with a status message.
"""

import os
import sys
import subprocess

def open_log_file(app, log_file_path):
    """
    Open the given log file using the platform's default text viewer,
    and write a status message to the app's InfoBar if present.

    Args:
        app: The main GUI application instance. Must have an 'infobar'
             attribute with a set_message(str) method.
        log_file_path: Absolute path to the log file to open.
    """
    try:
        if sys.platform.startswith("darwin"):
            subprocess.call(["open", log_file_path])
        elif sys.platform.startswith("win"):
            os.startfile(log_file_path)
        else:
            subprocess.call(["xdg-open", log_file_path])
        # Notify success
        if hasattr(app, "infobar"):
            app.infobar.set_message(f"Opened log file: {log_file_path}")
    except Exception as e:
        # Notify failure
        if hasattr(app, "infobar"):
            app.infobar.set_message(f"Error opening log file: {e}")
