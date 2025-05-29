#!/usr/bin/env python3
"""
batch_export_logs.py

Batch‐export your entire logs/ directory into a single ZIP.
"""
import os
import datetime
import zipfile
from tkinter import filedialog

def batch_export_logs(app, base_log_file: str):
    logs_dir = os.path.dirname(base_log_file)
    if not os.path.isdir(logs_dir):
        app.infobar.set_message(f"No logs folder at {logs_dir}")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")
    default_zip = f"gcloud_logs_{today}.zip"
    dest = filedialog.asksaveasfilename(
        title="Batch Export Logs",
        defaultextension=".zip",
        filetypes=[("Zip Archives","*.zip"),("All Files","*.*")],
        initialfile=default_zip
    )
    if not dest:
        return

    app.infobar.set_message(f"Exporting logs to {dest}…")
    try:
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
            for dirpath, _, files in os.walk(logs_dir):
                for f in files:
                    full = os.path.join(dirpath, f)
                    rel  = os.path.relpath(full, logs_dir)
                    zf.write(full, arcname=rel)
                    app._append_log(f"⋯ added {rel}\n")
        app.infobar.set_message(f"All logs exported to {dest}")
    except Exception as e:
        app.infobar.set_message(f"Batch export failed: {e}")
        app._append_log(f"Error: {e}\n")
