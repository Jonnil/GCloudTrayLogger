#!/usr/bin/env python3
"""
export_logs.py

Helper to export the application's current log file to a user-chosen location.
Opens a save dialog, performs the copy, and writes status to the InfoBar.
"""

import os
import shutil
import tkinter as tk
from tkinter import filedialog


def export_logs(app, log_file_path):
    """
    Prompt the user for a destination filename and copy the log file there.

    Args:
        app: The main application instance. Must have an 'infobar' attribute
             with a set_message(str) method.
        log_file_path: The absolute path to the current log file.
    """
    try:
        # Use the app window as the parent for the file dialog
        parent = app if isinstance(app, tk.Tk) else None

        dest = filedialog.asksaveasfilename(
            parent=parent,
            title="Export Logs As...",
            defaultextension=os.path.splitext(log_file_path)[1],
            filetypes=[("Log Files", "*.log"), ("All Files", "*.*")],
            initialfile=os.path.basename(log_file_path)
        )
        if not dest:
            return  # user cancelled

        shutil.copyfile(log_file_path, dest)
        if hasattr(app, "infobar"):
            app.infobar.set_message(f"Logs exported to {dest}")

    except Exception as e:
        if hasattr(app, "infobar"):
            app.infobar.set_message(f"Export logs failed: {e}")
