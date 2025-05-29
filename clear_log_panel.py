#!/usr/bin/env python3
"""
clear_log_panel.py

Helper to clear the application's log panel and update the InfoBar.
"""

def clear_log_panel(app):
    """
    Clears all text from the app's log panel (a ScrolledText widget)
    and writes a confirmation message to the InfoBar if present.

    Args:
        app: The main application instance. Must have:
             - app.log_panel : a tk.Text or ScrolledText widget
             - app.infobar   : an InfoBar instance with set_message(), optional
    """
    # Clear the log panel
    panel = getattr(app, 'log_panel', None)
    if panel:
        try:
            panel.config(state='normal')
            panel.delete('1.0', 'end')
            panel.config(state='disabled')
        except Exception:
            # silently ignore if panel not ready
            pass

    # Notify via InfoBar
    infobar = getattr(app, 'infobar', None)
    if infobar:
        try:
            infobar.set_message("Log panel cleared")
        except Exception:
            pass
