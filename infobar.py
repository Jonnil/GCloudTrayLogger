# infobar.py
"""
InfoBar widget for GCloud Tray Logger GUI.
A non-modal, persistent information bar that displays non-critical messages
at the bottom of the main window until updated.
"""
import tkinter as tk
from tkinter import ttk

class InfoBar(ttk.Frame):
    """
    A bottom-of-window info bar that shows status messages persistently until changed.
    Usage:
        infobar = InfoBar(parent)
        infobar.grid(row=1, column=0, sticky="ew")
        infobar.set_message("Ready")
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        # configure style
        self.configure(relief="sunken", padding=(5,2))
        # label to display message
        self._message_var = tk.StringVar(value="")
        self._label = ttk.Label(self, textvariable=self._message_var, anchor="w")
        self._label.pack(fill="x", expand=True)

    def set_message(self, message: str):
        """
        Update the info bar text. Message will persist until changed again.
        """
        self._message_var.set(message)

    def clear(self):
        """
        Clear the info bar text.
        """
        self._message_var.set("")
