#!/usr/bin/env python3
"""
app.py

Main GUI application for GCloud Tray Logger,
with support for daily log files (one per date) in monthly subfolders,
modular helpers for clearing, opening, and exporting logs,
a "Launch at system startup" option,
and a "Start in tray on launch" option.
"""
import threading
import queue
import os
import sys
import subprocess
import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import pystray
from PIL import Image, ImageDraw
import webbrowser

from manual import show_manual
from menu_bar import create_menu
from preferences import load_config, save_config
from infobar import InfoBar
from tooltip import ToolTip
from tailer import tail_logs
from logger_setup import setup_logger
from cloud_utils import open_cloud_settings
from startup_utils import enable_run_on_startup
from install_gcloud_sdk import install_gcloud_sdk

from clear_log_panel import clear_log_panel as clear_log_panel_helper
from open_log_file    import open_log_file    as open_log_file_helper
from export_logs      import export_logs      as export_logs_helper

# ─── Load & apply saved preferences ───────────────────────────
cfg = load_config()
BASE_LOG_FILE    = cfg["log_file"]
MAX_LOG_SIZE     = cfg["max_log_size"]
BACKUP_COUNT     = cfg["backup_count"]
LOG_PER_DATE     = cfg.get("log_per_date", False)
RUN_ON_STARTUP   = cfg.get("run_on_startup", False)
START_MINIMIZED  = cfg.get("start_minimized", False)
default_project  = cfg["default_project"]

def compute_effective_logfile(base_path: str, daily: bool) -> str:
    """
    If daily=False, return base_path.
    If daily=True, place file in logs/YYYY-MM/ and name it basename-YYYY-MM-DD.ext.
    """
    if not daily:
        return base_path

    log_dir = os.path.dirname(base_path)
    today = datetime.date.today()
    month_folder = today.strftime("%Y-%m")
    monthly_dir = os.path.join(log_dir, month_folder)
    os.makedirs(monthly_dir, exist_ok=True)

    root, ext = os.path.splitext(os.path.basename(base_path))
    dated_name = f"{root}-{today.strftime('%Y-%m-%d')}{ext}"
    return os.path.join(monthly_dir, dated_name)

# Compute the initial effective path
EFFECTIVE_LOG_FILE = compute_effective_logfile(BASE_LOG_FILE, LOG_PER_DATE)

# Set up logger & handler
logger, _handler = setup_logger(
    EFFECTIVE_LOG_FILE,
    MAX_LOG_SIZE,
    BACKUP_COUNT,
    log_per_date=False
)

# ─── Globals ───────────────────────────────────────────────────
_stop_event    = threading.Event()
_gcloud_thread = None
_log_queue     = queue.Queue()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GCloud Tray Logger")

        # fix #1: initialize tray_icon before any hide_to_tray call
        self.tray_icon = None

        # keep track of current effective log file
        self._effective_file = EFFECTIVE_LOG_FILE

        # Layout: content frame at row0, infobar at row1
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        create_menu(self)
        self._build_widgets()

        # optionally start minimized
        if START_MINIMIZED:
            self.hide_to_tray()

        self.after(100, self._poll_log_queue)

    def _build_widgets(self):
        frm = ttk.Frame(self, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")
        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(6, weight=1)

        # Row 0: Project ID + Buttons
        ttk.Label(frm, text="Project ID:").grid(row=0, column=0, sticky="w")
        self.project_var = tk.StringVar(value=default_project)
        proj_entry = ttk.Entry(frm, textvariable=self.project_var, width=30)
        proj_entry.grid(row=0, column=1, sticky="ew")
        ToolTip(proj_entry,
                "Enter your GCP Project ID (e.g. 'my-project-12345').\n"
                "Find it under IAM & Admin → Settings in the Cloud Console.")
        ttk.Button(frm, text="Open Cloud Settings",
                   command=self._open_cloud_settings).grid(row=0, column=2, padx=(5,0))
        ttk.Button(frm, text="Install gcloud SDK",
                   command=self._install_gcloud_sdk).grid(row=0, column=3, padx=(5,0))
        proj_entry.bind("<FocusOut>", lambda e: self._save_and_apply())
        proj_entry.bind("<Return>",   lambda e: self._save_and_apply())

        # Row 1: Log File Path + Browse
        ttk.Label(frm, text="Log File Path:")\
            .grid(row=1, column=0, sticky="w", pady=(5,0))
        self.log_file_var = tk.StringVar(value=BASE_LOG_FILE)
        log_entry = ttk.Entry(frm, textvariable=self.log_file_var, width=30)
        log_entry.grid(row=1, column=1, sticky="ew", pady=(5,0))
        ToolTip(log_entry, "Where the logs are written/rotated.")
        ttk.Button(frm, text="Browse…", command=self._browse_log_file)\
           .grid(row=1, column=2, padx=(5,0), pady=(5,0))
        log_entry.bind("<FocusOut>", lambda e: self._save_and_apply())

        # Row 2: Daily logs checkbox
        self.log_per_date_var = tk.BooleanVar(value=LOG_PER_DATE)
        ttk.Checkbutton(
            frm,
            text="Daily log files (one file per date)",
            variable=self.log_per_date_var,
            command=self._save_and_apply
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(5,0))

        # Row 3: Launch at startup checkbox
        self.startup_var = tk.BooleanVar(value=RUN_ON_STARTUP)
        ttk.Checkbutton(
            frm,
            text="Launch at system startup",
            variable=self.startup_var,
            command=self._save_and_apply
        ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(5,0))

        # Row 4: Start in tray on launch checkbox
        self.minimize_var = tk.BooleanVar(value=START_MINIMIZED)
        ttk.Checkbutton(
            frm,
            text="Start minimized to tray",
            variable=self.minimize_var,
            command=self._save_and_apply
        ).grid(row=4, column=0, columnspan=4, sticky="w", pady=(5,0))

        # Row 5: Control Buttons
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=5, column=0, columnspan=4, pady=(10,10))
        self.start_btn = ttk.Button(btn_frame, text="Start Logging",
                                    command=self.start_logging)
        self.start_btn.grid(row=0, column=0, padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="Stop Logging",
                                   command=self.stop_logging, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Exit", command=self.exit_app)\
            .grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Send to Tray", command=self.hide_to_tray)\
            .grid(row=0, column=3, padx=5)

        # Row 6: Log Output Panel
        self.log_panel = scrolledtext.ScrolledText(frm, height=20, state="disabled")
        self.log_panel.grid(row=6, column=0, columnspan=4, sticky="nsew")

        # InfoBar (below)
        self.infobar = InfoBar(self)
        self.infobar.grid(row=1, column=0, sticky="ew", columnspan=1)
        self.infobar.set_message("Ready")

    # ─── Helpers ─────────────────────────────────────────────────
    def _browse_log_file(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log Files","*.log"),("All Files","*.*")],
            initialfile=os.path.basename(self.log_file_var.get())
        )
        if dest:
            self.log_file_var.set(dest)
            self._save_and_apply()

    def _save_and_apply(self):
        new_cfg = {
            "default_project": self.project_var.get().strip(),
            "log_file"       : self.log_file_var.get().strip(),
            "max_log_size"   : MAX_LOG_SIZE,
            "backup_count"   : BACKUP_COUNT,
            "log_per_date"   : self.log_per_date_var.get(),
            "run_on_startup" : self.startup_var.get(),
            "start_minimized": self.minimize_var.get()
        }
        save_config(new_cfg)

        # recompute effective path
        eff = compute_effective_logfile(new_cfg["log_file"], new_cfg["log_per_date"])
        self._effective_file = eff

        # reconfigure logger
        global logger, _handler
        logger, _handler = setup_logger(
            eff,
            new_cfg["max_log_size"],
            new_cfg["backup_count"],
            log_per_date=False
        )

        # toggle startup
        enable_run_on_startup(new_cfg["run_on_startup"])

        # apply minimize setting
        if new_cfg["start_minimized"]:
            self.hide_to_tray()
        else:
            if self.tray_icon:
                self.show_from_tray()

        self.infobar.set_message("Settings saved")

    def _open_cloud_settings(self):
        open_cloud_settings(self.project_var.get().strip(), self.infobar)

    def _install_gcloud_sdk(self):
        """
        Kick off the background installer and hook up
        its output to the log panel and infobar.
        """
        install_gcloud_sdk(
            # send each stdout line into the log panel
            output_callback=lambda line: self._append_log(line),
            # send status updates into the infobar
            status_callback=lambda msg: self.infobar.set_message(msg)
        )

    # ─── Log Tailing ───────────────────────────────────────────
    def start_logging(self):
        proj = self.project_var.get().strip()
        if not proj:
            self.infobar.set_message("Error: Missing Project ID")
            return

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        _stop_event.clear()

        global _gcloud_thread
        _gcloud_thread = threading.Thread(
            target=tail_logs,
            args=(proj, _log_queue, _stop_event),
            daemon=True
        )
        _gcloud_thread.start()

        self.infobar.set_message(f"Started logging for project: {proj}")
        self._append_log(f"-- Started logging for project: {proj} --\n")

    def stop_logging(self):
        self.stop_btn.config(state="disabled")
        _stop_event.set()
        self.start_btn.config(state="normal")
        self.infobar.set_message("Logging stopped")

    # ─── Clear / Open / Export Logs ─────────────────────────────
    def clear_log_panel(self):
        clear_log_panel_helper(self)

    def open_log_file(self):
        open_log_file_helper(self, self._effective_file)

    def export_logs(self):
        export_logs_helper(self, self._effective_file)

    # ─── Log Panel Helpers ─────────────────────────────────────
    def _append_log(self, txt: str):
        self.log_panel.config(state="normal")
        self.log_panel.insert(tk.END, txt)
        self.log_panel.see(tk.END)
        self.log_panel.config(state="disabled")

    def _poll_log_queue(self):
        try:
            while True:
                self._append_log(_log_queue.get_nowait())
        except queue.Empty:
            pass
        self.after(100, self._poll_log_queue)

    # ─── Tray Integration ──────────────────────────────────────
    def hide_to_tray(self):
        # fix #2: use getattr to check existence
        if getattr(self, "tray_icon", None) is None:
            menu = pystray.Menu(
                pystray.MenuItem("Show", lambda: self.show_from_tray()),
                pystray.MenuItem("Exit", lambda: self.exit_app())
            )
            icon = self._create_icon()
            self.tray_icon = pystray.Icon("GCloudTrayLogger", icon, "GCloud Tray Logger", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        self.withdraw()

    def show_from_tray(self):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.deiconify()

    # ─── Exit ──────────────────────────────────────────────────
    def exit_app(self):
        _stop_event.set()
        self.destroy()
        sys.exit(0)

    def _create_icon(self):
        img = Image.new("RGB", (64, 64), color=(0, 122, 204))
        d = ImageDraw.Draw(img)
        d.text((20, 20), "☁", fill=(255, 255, 255))
        return img


if __name__ == "__main__":
    app = App()
    app.mainloop()
