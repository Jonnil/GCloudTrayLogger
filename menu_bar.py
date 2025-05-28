#!/usr/bin/env python3
"""
Menu bar definition for GCloud Tray Logger GUI.
Provides a reusable create_menu(root) function to attach a menu bar to any Tkinter window.
"""
import tkinter as tk
from manual import show_manual


def create_menu(root):
    """
    Build and attach the menu bar to the given root window.
    """
    menubar = tk.Menu(root)

    # helper to safely call root methods
    def _action(method_name):
        def _inner(*args, **kwargs):
            method = getattr(root, method_name, None)
            if callable(method):
                return method()
            else:
                # optional: log or warn about missing implementation
                print(f"Menu action '{method_name}' is not implemented.")
        return _inner

    # File menu
    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Start Logging", accelerator="Ctrl+R", command=_action('start_logging'))
    filemenu.add_command(label="Stop Logging", accelerator="Ctrl+T", command=_action('stop_logging'))
    filemenu.add_command(label="Clear Log Panel", accelerator="Ctrl+L", command=_action('clear_log_panel'))
    filemenu.add_separator()
    filemenu.add_command(label="Open Log File…", accelerator="Ctrl+O", command=_action('open_log_file'))
    filemenu.add_command(label="Export Logs…", accelerator="Ctrl+E", command=_action('export_logs'))
    filemenu.add_separator()
    filemenu.add_command(label="Exit", accelerator="Ctrl+Q", command=_action('exit_app'))
    menubar.add_cascade(label="File", menu=filemenu)

    # Help menu
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Manual", accelerator="F1", command=lambda: show_manual(root))
    menubar.add_cascade(label="Help", menu=helpmenu)

    # Attach menu bar
    root.config(menu=menubar)

    # Keyboard shortcuts
    shortcuts = [
        ('<Control-r>', 'start_logging'),
        ('<Control-R>', 'start_logging'),
        ('<Control-t>', 'stop_logging'),
        ('<Control-T>', 'stop_logging'),
        ('<Control-l>', 'clear_log_panel'),
        ('<Control-L>', 'clear_log_panel'),
        ('<Control-o>', 'open_log_file'),
        ('<Control-O>', 'open_log_file'),
        ('<Control-e>', 'export_logs'),
        ('<Control-E>', 'export_logs'),
        ('<Control-p>', 'open_preferences'),
        ('<Control-P>', 'open_preferences'),
        ('<Control-q>', 'exit_app'),
        ('<Control-Q>', 'exit_app'),
        ('<F1>', None),  # manual handled separately
    ]
    for key, method in shortcuts:
        if method:
            root.bind_all(key, lambda e, m=method: _action(m)())
        else:
            root.bind_all(key, lambda e: show_manual(root))
