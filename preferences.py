#!/usr/bin/env python3
"""
preferences.py

Preferences for GCloud Tray Logger.
Loads and saves user settings to a JSON file in the user's AppData (Windows)
or ~/.config (Unix), under GCloudTrayLogger/GCloudTrayLogger_preferences.json.
Also defaults the log file itself to reside inside that same directory.
"""

import json
import os
import tkinter as tk
from tkinter import ttk

# ─── Determine config & logs directory ─────────────────────────
if os.name == 'nt':
    BASE_CONFIG_DIR = os.getenv('APPDATA', os.path.expanduser('~'))
else:
    BASE_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config')

CONFIG_DIR       = os.path.join(BASE_CONFIG_DIR, 'GCloudTrayLogger')
PREFERENCES_FILE = os.path.join(CONFIG_DIR, 'GCloudTrayLogger_preferences.json')
LOGS_DIR         = os.path.join(CONFIG_DIR, 'logs')
DEFAULT_LOG_FILE = os.path.join(LOGS_DIR, 'gcloud_tray_logger.log')

# ─── Default settings ─────────────────────────────────────────
DEFAULTS = {
    "default_project"   : os.environ.get("GCLOUD_PROJECT", "your-project-id"),
    "log_file"          : DEFAULT_LOG_FILE,
    "max_log_size"      : 5 * 1024 * 1024,
    "backup_count"      : 3,
    "log_per_date"      : True,
    "run_on_startup"    : False,
    "start_minimized"   : False,
    "auto_start_logging": False,
}


def load_config():
    """
    Load settings from PREFERENCES_FILE, or return a copy of DEFAULTS.
    Ensures CONFIG_DIR and LOGS_DIR exist, and makes log_file absolute.
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    if os.path.exists(PREFERENCES_FILE):
        try:
            with open(PREFERENCES_FILE, 'r') as f:
                data = json.load(f)
            # Fill in any missing keys
            for key, default in DEFAULTS.items():
                data.setdefault(key, default)
        except Exception:
            data = DEFAULTS.copy()
    else:
        data = DEFAULTS.copy()

    # Normalize log_file path
    lf = data.get("log_file", DEFAULT_LOG_FILE)
    if not os.path.isabs(lf):
        lf = os.path.join(CONFIG_DIR, lf)
    os.makedirs(os.path.dirname(lf), exist_ok=True)
    data["log_file"] = lf

    return data


def save_config(config: dict):
    """
    Save the given settings dict to PREFERENCES_FILE.
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    with open(PREFERENCES_FILE, 'w') as f:
        json.dump(config, f, indent=4)


def show_preferences(parent=None, on_save=None):
    """
    Dialog to edit preferences.
    Calls on_save(updated_config) if provided.
    """
    cfg = load_config()

    win = tk.Toplevel(parent) if parent else tk.Tk()
    win.title("Preferences")
    win.geometry("450x380")
    if parent:
        win.transient(parent)
        win.grab_set()

    # ── Default Project ID ────────────────────────────────────
    ttk.Label(win, text="Default Project ID:")\
        .grid(row=0, column=0, sticky="w", padx=10, pady=5)
    proj_var = tk.StringVar(value=cfg["default_project"])
    ttk.Entry(win, textvariable=proj_var, width=40)\
        .grid(row=0, column=1, padx=10, pady=5)

    # ── Log file path ─────────────────────────────────────────
    ttk.Label(win, text="Log File Path:")\
        .grid(row=1, column=0, sticky="w", padx=10, pady=5)
    log_var = tk.StringVar(value=cfg["log_file"])
    ttk.Entry(win, textvariable=log_var, width=40)\
        .grid(row=1, column=1, padx=10, pady=5)

    # ── Max log size ──────────────────────────────────────────
    ttk.Label(win, text="Max Log Size (bytes):")\
        .grid(row=2, column=0, sticky="w", padx=10, pady=5)
    size_var = tk.IntVar(value=cfg["max_log_size"])
    ttk.Entry(win, textvariable=size_var, width=40)\
        .grid(row=2, column=1, padx=10, pady=5)

    # ── Backup count ──────────────────────────────────────────
    ttk.Label(win, text="Backup Count:")\
        .grid(row=3, column=0, sticky="w", padx=10, pady=5)
    back_var = tk.IntVar(value=cfg["backup_count"])
    ttk.Entry(win, textvariable=back_var, width=40)\
        .grid(row=3, column=1, padx=10, pady=5)

    # ── Daily logs checkbox ───────────────────────────────────
    logdate_var = tk.BooleanVar(value=cfg["log_per_date"])
    ttk.Checkbutton(
        win,
        text="One log file per day",
        variable=logdate_var
    ).grid(row=4, column=1, sticky="w", padx=10, pady=5)

    # ── Run on startup checkbox ───────────────────────────────
    startup_var = tk.BooleanVar(value=cfg["run_on_startup"])
    ttk.Checkbutton(
        win,
        text="Launch at system startup",
        variable=startup_var
    ).grid(row=5, column=1, sticky="w", padx=10, pady=5)

    # ── Start minimized checkbox ──────────────────────────────
    mini_var = tk.BooleanVar(value=cfg["start_minimized"])
    ttk.Checkbutton(
        win,
        text="Start minimized to tray",
        variable=mini_var
    ).grid(row=6, column=1, sticky="w", padx=10, pady=5)

    # ── Auto-start logging checkbox ───────────────────────────
    auto_var = tk.BooleanVar(value=cfg["auto_start_logging"])
    ttk.Checkbutton(
        win,
        text="Auto-start logging on launch",
        variable=auto_var
    ).grid(row=7, column=1, sticky="w", padx=10, pady=5)

    # ── Buttons ───────────────────────────────────────────────
    btn_frame = ttk.Frame(win)
    btn_frame.grid(row=8, column=0, columnspan=2, pady=20)

    def on_ok():
        new_cfg = {
            "default_project"   : proj_var.get().strip(),
            "log_file"          : log_var.get().strip(),
            "max_log_size"      : size_var.get(),
            "backup_count"      : back_var.get(),
            "log_per_date"      : logdate_var.get(),
            "run_on_startup"    : startup_var.get(),
            "start_minimized"   : mini_var.get(),
            "auto_start_logging": auto_var.get(),
        }
        save_config(new_cfg)
        if callable(on_save):
            on_save(new_cfg)
        win.destroy()

    def on_cancel():
        win.destroy()

    ttk.Button(btn_frame, text="OK",     command=on_ok)\
        .grid(row=0, column=0, padx=10)
    ttk.Button(btn_frame, text="Cancel", command=on_cancel)\
        .grid(row=0, column=1, padx=10)

    if not parent:
        win.mainloop()


if __name__ == '__main__':
    show_preferences()
