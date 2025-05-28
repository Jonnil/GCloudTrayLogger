#!/usr/bin/env python3
"""
tooltip.py

Tooltip widget for Tkinter.

Provides a ToolTip class that adds a tooltip to any Tkinter widget.

Usage:
    from tooltip import ToolTip
    entry = ttk.Entry(...)
    entry.pack()
    ToolTip(entry, "This is your tooltip text.")
"""

import tkinter as tk

class ToolTip:
    """
    Create a tooltip for a given widget.
    
    Parameters:
    - widget: Tkinter widget to attach the tooltip to.
    - text: text to display inside the tooltip.
    - delay: time in milliseconds before tooltip appears (default 500).
    - bg: background color of tooltip (default light yellow).
    - fg: text color of tooltip (default black).
    - wraplength: max line length before wrapping (default 300 pixels).
    """
    def __init__(self, widget, text,
                 delay=500,
                 bg="#ffffe0",
                 fg="#000000",
                 wraplength=300):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.bg = bg
        self.fg = fg
        self.wraplength = wraplength
        self.tipwindow = None
        self.id = None
        # Bind events
        self.widget.bind("<Enter>", self._on_enter, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<ButtonPress>", self._on_leave, add="+")
        self.widget.bind("<Destroy>", self._on_leave, add="+")

    def _on_enter(self, event=None):
        self._schedule()

    def _on_leave(self, event=None):
        self._unschedule()
        self._hide()

    def _schedule(self):
        self._unschedule()
        self.id = self.widget.after(self.delay, self._show)

    def _unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def _show(self):
        if self.tipwindow or not self.text:
            return
        # Calculate position: just below and to the right of the widget
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1

        # Create tooltip window
        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(background=self.bg)

        # Tooltip label
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background=self.bg,
            foreground=self.fg,
            relief=tk.SOLID,
            borderwidth=1,
            wraplength=self.wraplength
        )
        label.pack(ipadx=4, ipady=2)

        # Ensure it's on top
        tw.lift()
        try:
            tw.attributes("-topmost", True)
        except Exception:
            pass

        self.tipwindow = tw

    def _hide(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None
