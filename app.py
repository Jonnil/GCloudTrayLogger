# app.py
import threading
import queue
import shutil
import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import pystray
from PIL import Image, ImageDraw

from manual import show_manual
from menu_bar import create_menu
from preferences import load_config, save_config
from infobar import InfoBar
from tooltip import ToolTip
from tailer import tail_logs
from logger_setup import setup_logger
from cloud_utils import open_cloud_settings

# ─── Load & apply saved preferences ───────────────────────────
config = load_config()
LOG_FILE        = config["log_file"]
MAX_LOG_SIZE    = config["max_log_size"]
BACKUP_COUNT    = config["backup_count"]
default_project = config["default_project"]

logger, _handler = setup_logger(LOG_FILE, MAX_LOG_SIZE, BACKUP_COUNT)

# ─── Globals ───────────────────────────────────────────────────
_stop_event    = threading.Event()
_gcloud_thread = None
_log_queue     = queue.Queue()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GCloud Tray Logger")

        # Layout: main grid + infobar row
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        create_menu(self)
        self._build_widgets()
        self.after(100, self._poll_log_queue)

        self.tray_icon = None

    def _build_widgets(self):
        frm = ttk.Frame(self, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")
        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(3, weight=1)

        # ── Row 0: Project ID + Settings Button ───────────────────
        ttk.Label(frm, text="Project ID:").grid(row=0, column=0, sticky="w")
        self.project_var  = tk.StringVar(value=default_project)
        proj_entry        = ttk.Entry(frm, textvariable=self.project_var, width=30)
        proj_entry.grid(row=0, column=1, sticky="ew")
        ToolTip(proj_entry,
                "Enter your GCP Project ID (e.g. 'my-project-12345').\n"
                "Find it in the Cloud Console header or under IAM & Admin → Settings.")
        ttk.Button(frm, text="Open Cloud Settings",
                   command=self._open_cloud_settings)\
           .grid(row=0, column=2, padx=(5,0))

        # Bind saving on change
        proj_entry.bind("<FocusOut>",      lambda e: self._save_and_apply())
        proj_entry.bind("<Return>",        lambda e: self._save_and_apply())

        # ── Row 1: Log File Path + Browse ─────────────────────────
        ttk.Label(frm, text="Log File Path:")\
            .grid(row=1, column=0, sticky="w", pady=(5,0))
        self.log_file_var = tk.StringVar(value=LOG_FILE)
        log_entry         = ttk.Entry(frm, textvariable=self.log_file_var, width=30)
        log_entry.grid(row=1, column=1, sticky="ew", pady=(5,0))
        ToolTip(log_entry,
                "Path where the gcloud output is written and rotated.")
        ttk.Button(frm, text="Browse…", command=self._browse_log_file)\
           .grid(row=1, column=2, padx=(5,0), pady=(5,0))
        log_entry.bind("<FocusOut>", lambda e: self._save_and_apply())

        # ── Row 2: Control Buttons ─────────────────────────────────
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=(10,10))
        self.start_btn = ttk.Button(btn_frame, text="Start Logging",
                                    command=self.start_logging)
        self.start_btn.grid(row=0, column=0, padx=5)
        self.stop_btn  = ttk.Button(btn_frame, text="Stop Logging",
                                    command=self.stop_logging, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Exit", command=self.exit_app)\
            .grid(row=0, column=2, padx=5)

        # ── Row 3: Log Output Panel ────────────────────────────────
        self.log_panel = scrolledtext.ScrolledText(frm, height=20, state="disabled")
        self.log_panel.grid(row=3, column=0, columnspan=3, sticky="nsew")

        # ── Row 4: Persistent InfoBar ─────────────────────────────
        self.infobar = InfoBar(self)
        self.infobar.grid(row=1, column=0, sticky="ew", columnspan=1)
        self.infobar.set_message("Ready")

    # ─── Settings & Persistence ─────────────────────────────────
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
        """
        Read current project & log-file, save to disk, and reconfigure logger.
        """
        new_cfg = {
            "default_project": self.project_var.get().strip(),
            "log_file"       : self.log_file_var.get().strip(),
            "max_log_size"   : MAX_LOG_SIZE,
            "backup_count"   : BACKUP_COUNT
        }
        # persist
        save_config(new_cfg)

        # apply to logger
        global LOG_FILE, _handler
        LOG_FILE = new_cfg["log_file"]
        logger.removeHandler(_handler)
        _handler.close()
        logger, _handler = setup_logger(
            new_cfg["log_file"],
            new_cfg["max_log_size"],
            new_cfg["backup_count"]
        )

        self.infobar.set_message("Settings saved")

    # ─── Cloud Settings ────────────────────────────────────────
    def _open_cloud_settings(self):
        open_cloud_settings(self.project_var.get().strip(), self.infobar)

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

    # ─── Log Panel Helpers ─────────────────────────────────────
    def _append_log(self, text: str):
        self.log_panel.config(state="normal")
        self.log_panel.insert(tk.END, text)
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
        if not self.tray_icon:
            img = self._create_icon()
            menu = pystray.Menu(
                pystray.MenuItem("Show", lambda: self.show_from_tray()),
                pystray.MenuItem("Exit", lambda: self.exit_app())
            )
            self.tray_icon = pystray.Icon(
                "GCloudTrayLogger", img, "GCloud Tray Logger", menu
            )
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
        d   = ImageDraw.Draw(img)
        d.text((20, 20), "☁", fill=(255,255,255))
        return img
