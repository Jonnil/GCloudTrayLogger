#!/usr/bin/env python3
"""
app.py

Main GUI application for GCloud Tray Logger,
with support for:
  - daily log files (one per date) in monthly subfolders,
  - modular helpers for clearing, opening, and exporting logs,
  - “Launch at system startup”
  - “Start in tray on launch”
  - “Auto-start logging on launch”
  - Juni sprite animation showing sad/happy states.
"""
import threading
import queue
import os
import sys
import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import pystray
from PIL import Image, ImageDraw

from manual               import show_manual
from menu_bar            import create_menu
from preferences         import load_config, save_config
from infobar             import InfoBar
from tooltip             import ToolTip
from tailer              import tail_logs
from logger_setup        import setup_logger
from cloud_utils         import open_cloud_settings
from startup_utils       import enable_run_on_startup
from install_gcloud_sdk  import install_gcloud_sdk
from sprite_animator     import SpriteAnimator
from gcloud_auth_login import gcloud_auth_login

from clear_log_panel     import clear_log_panel   as clear_log_panel_helper
from open_log_file       import open_log_file      as open_log_file_helper
from export_logs         import export_logs        as export_logs_helper
from batch_export_logs   import batch_export_logs  as batch_export_logs_helper

# ─── Load & apply saved preferences ───────────────────────────
cfg = load_config()
BASE_LOG_FILE      = cfg["log_file"]
MAX_LOG_SIZE       = cfg["max_log_size"]
BACKUP_COUNT       = cfg["backup_count"]
LOG_PER_DATE       = cfg.get("log_per_date", False)
RUN_ON_STARTUP     = cfg.get("run_on_startup", False)
START_MINIMIZED    = cfg.get("start_minimized", False)
AUTO_START_LOGGING = cfg.get("auto_start_logging", False)
default_project    = cfg["default_project"]

def compute_effective_logfile(base_path: str, daily: bool) -> str:
    if not daily:
        return base_path
    log_dir = os.path.dirname(base_path)
    today   = datetime.date.today()
    month_dir = os.path.join(log_dir, today.strftime("%Y-%m"))
    os.makedirs(month_dir, exist_ok=True)
    root, ext = os.path.splitext(os.path.basename(base_path))
    dated     = f"{root}-{today.strftime('%Y-%m-%d')}{ext}"
    return os.path.join(month_dir, dated)

# initial effective log file
EFFECTIVE_LOG_FILE = compute_effective_logfile(BASE_LOG_FILE, LOG_PER_DATE)

# set up rotating logger
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

        # initial state
        self.tray_icon      = None
        self._effective_file = EFFECTIVE_LOG_FILE

        # grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        create_menu(self)
        self._build_widgets()

        # handle startup prefs
        if START_MINIMIZED:
            self.hide_to_tray()
        if AUTO_START_LOGGING:
            self.start_logging()

        self.after(100, self._poll_log_queue)

    def _build_widgets(self):
        frm = ttk.Frame(self, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")
        # columns 0–3 hold your main controls; column 1 expands for the entry
        frm.columnconfigure(0, weight=0)
        frm.columnconfigure(1, weight=1)
        frm.columnconfigure(2, weight=0)
        frm.columnconfigure(3, weight=0)
        # column 4 is our sprite column—never expands
        frm.columnconfigure(4, weight=0)
        frm.rowconfigure(7, weight=1)

        # ── Row 0: Project ID + tools
        ttk.Label(frm, text="Project ID:").grid(row=0, column=0, sticky="w")
        self.project_var = tk.StringVar(value=default_project)
        proj_entry = ttk.Entry(frm, textvariable=self.project_var, width=30)
        proj_entry.grid(row=0, column=1, sticky="ew")
        ToolTip(proj_entry,
            "Enter your GCP Project ID (e.g. 'my-project-12345').\n"
            "Find it under IAM & Admin → Settings in the Cloud Console."
        )
        ttk.Button(frm, text="Open Cloud Settings", command=self._open_cloud_settings)\
            .grid(row=0, column=2, padx=5)
        ttk.Button(frm, text="Install gcloud SDK", command=self._install_gcloud_sdk)\
            .grid(row=0, column=3, padx=5)
        ttk.Button(frm, text="Authenticate…",
            command=lambda: gcloud_auth_login(
                project_id=self.project_var.get().strip(),
                output_callback=self._append_log,
                status_callback=lambda msg: self.infobar.set_message(msg)
            )
        ).grid(row=0, column=4, padx=5)

        proj_entry.bind("<FocusOut>", lambda e: self._save_and_apply())
        proj_entry.bind("<Return>",   lambda e: self._save_and_apply())

        # ── Row 1: Log File Path
        ttk.Label(frm, text="Log File Path:").grid(row=1, column=0, sticky="w", pady=(5,0))
        self.log_file_var = tk.StringVar(value=BASE_LOG_FILE)
        log_entry = ttk.Entry(frm, textvariable=self.log_file_var, width=30)
        log_entry.grid(row=1, column=1, sticky="ew", pady=(5,0))
        ToolTip(log_entry, "Where the logs are written/rotated.")
        ttk.Button(frm, text="Browse…", command=self._browse_log_file)\
            .grid(row=1, column=2, padx=5, pady=(5,0))
        log_entry.bind("<FocusOut>", lambda e: self._save_and_apply())

        # ── Row 2: Daily logs
        self.log_per_date_var = tk.BooleanVar(value=LOG_PER_DATE)
        ttk.Checkbutton(frm,
            text="Daily log files (one file per date)",
            variable=self.log_per_date_var,
            command=self._save_and_apply
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(5,0))

        # ── Row 3: Launch at startup
        self.startup_var = tk.BooleanVar(value=RUN_ON_STARTUP)
        ttk.Checkbutton(frm,
            text="Launch at system startup",
            variable=self.startup_var,
            command=self._save_and_apply
        ).grid(row=3, column=0, columnspan=4, sticky="w")

        # ── Row 4: Start minimized
        self.minimize_var = tk.BooleanVar(value=START_MINIMIZED)
        ttk.Checkbutton(frm,
            text="Start minimized to tray",
            variable=self.minimize_var,
            command=self._save_and_apply
        ).grid(row=4, column=0, columnspan=4, sticky="w")

        # ── Row 5: Auto-start logging
        self.auto_start_var = tk.BooleanVar(value=AUTO_START_LOGGING)
        ttk.Checkbutton(frm,
            text="Auto-start logging on launch",
            variable=self.auto_start_var,
            command=self._save_and_apply
        ).grid(row=5, column=0, columnspan=4, sticky="w", pady=(0,5))

        # ── Row 6: Control buttons
        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=4, pady=10)
        self.start_btn = ttk.Button(btns, text="Start Logging", command=self.start_logging)
        self.start_btn.grid(row=0, column=0, padx=5)
        self.stop_btn  = ttk.Button(btns, text="Stop Logging", command=self.stop_logging, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=5)
        ttk.Button(btns, text="Exit", command=self.exit_app).grid(row=0, column=2, padx=5)
        ttk.Button(btns, text="Send to Tray", command=self.hide_to_tray).grid(row=0, column=3, padx=5)

        # create & place your sprite at any size:
        self.juni_sprite = SpriteAnimator(
            btns,
            sad_path="assets/juni_sad.png",
            happy_paths=[
                "assets/juni_happy1.png",
                "assets/juni_happy2.png"
            ],
            interval=800,
            size=(64, 100),        # scale
        )
        self.juni_sprite.grid(
            row=0,
            column=4,
            rowspan=2,
            sticky="sw",     # bottom-left of its cell
            padx=(5,0),
            pady=(0,5),
        )

        # ── Row 7: Log output panel
        self.log_panel = scrolledtext.ScrolledText(frm, height=20, state="disabled")
        self.log_panel.grid(row=7, column=0, columnspan=4, sticky="nsew")

        # ── InfoBar ──────────────────────────────────────────────
        self.infobar = InfoBar(self)
        self.infobar.grid(row=1, column=0, sticky="ew", columnspan=4)
        self.infobar.set_message("Ready")

    # ─── Settings persistence ────────────────────────────────────
    def _browse_log_file(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log Files","*.log"),("All","*.*")],
            initialfile=os.path.basename(self.log_file_var.get())
        )
        if dest:
            self.log_file_var.set(dest)
            self._save_and_apply()

    def _save_and_apply(self):
        new_cfg = {
            "default_project"   : self.project_var.get().strip(),
            "log_file"          : self.log_file_var.get().strip(),
            "max_log_size"      : MAX_LOG_SIZE,
            "backup_count"      : BACKUP_COUNT,
            "log_per_date"      : self.log_per_date_var.get(),
            "run_on_startup"    : self.startup_var.get(),
            "start_minimized"   : self.minimize_var.get(),
            "auto_start_logging": self.auto_start_var.get(),
        }
        save_config(new_cfg)

        # toggle run-on-startup in OS
        enable_run_on_startup(new_cfg["run_on_startup"])

        # recompute log path & reconfigure logger
        eff = compute_effective_logfile(new_cfg["log_file"], new_cfg["log_per_date"])
        self._effective_file = eff
        global logger, _handler
        logger, _handler = setup_logger(
            eff,
            new_cfg["max_log_size"],
            new_cfg["backup_count"],
            log_per_date=False
        )

        # handle start-minimized
        if new_cfg["start_minimized"]:
            self.hide_to_tray()
        else:
            if self.tray_icon:
                self.show_from_tray()

        self.infobar.set_message("Settings saved")

    # ─── Cloud settings ─────────────────────────────────────────
    def _open_cloud_settings(self):
        open_cloud_settings(self.project_var.get().strip(), self.infobar)

    # ─── SDK installer ──────────────────────────────────────────
    def _install_gcloud_sdk(self):
        install_gcloud_sdk(
            output_callback=lambda line: self._append_log(line),
            status_callback=lambda msg: self.infobar.set_message(msg)
        )

    # ─── Log tailing ────────────────────────────────────────────
    def start_logging(self):
        proj = self.project_var.get().strip()
        if not proj:
            self.infobar.set_message("Error: Missing Project ID")
            return

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        _stop_event.clear()
        # start sprite animation
        self.juni_sprite.start_animation()

        global _gcloud_thread
        _gcloud_thread = threading.Thread(
            target=tail_logs, args=(proj, _log_queue, _stop_event), daemon=True
        )
        _gcloud_thread.start()

        self.infobar.set_message(f"Started logging for project: {proj}")
        self._append_log(f"-- Started logging for project: {proj} --\n")

    def stop_logging(self):
        self.stop_btn.config(state="disabled")
        _stop_event.set()
        self.start_btn.config(state="normal")
        # show sad sprite
        self.juni_sprite.show_sad()
        self.infobar.set_message("Logging stopped")

    # ─── Clear / Open / Export / Batch-Export ─────────────────────
    def clear_log_panel(self):
        clear_log_panel_helper(self)

    def open_log_file(self):
        open_log_file_helper(self, self._effective_file)

    def export_logs(self):
        export_logs_helper(self, self._effective_file)

    def batch_export_logs(self):
        batch_export_logs_helper(self, BASE_LOG_FILE)

    # ─── Internal helpers ────────────────────────────────────────
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

    # ─── Tray integration ───────────────────────────────────────
    def hide_to_tray(self):
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
        img = Image.new("RGB", (64,64), color=(0,122,204))
        d   = ImageDraw.Draw(img)
        d.text((20,20),"☁", fill=(255,255,255))
        return img

if __name__ == "__main__":
    app = App()
    app.mainloop()
