# manual.py
"""
GCloud Tray Logger Manual
Provides a simple GUI window displaying usage instructions and help for the GCloud Tray Logger.
"""
import tkinter as tk
from tkinter import scrolledtext

MANUAL_TEXT = '''
GCloud Tray Logger Manual

Overview:
  GCloud Tray Logger is a lightweight Python application that tails your
  Google Cloud App Engine logs locally, displaying them in a GUI and
  optionally hiding in the system tray.

Features:
  • Enter your GCP project ID to start/stop log streaming
  • Live log window with scrollback and auto-follow
  • Rotating local log file (gcloud_tray_logger.log) with backups
  • System tray integration: minimize to tray, restore, or exit

Usage:
  1. Launch the application:
     python gcloud_tray_logger.py

  2. In the main window:
     – Enter your GCP project ID (or set $GCLOUD_PROJECT to default).
     – Click "Start Logging" to begin streaming logs.
     – Click "Stop Logging" to end streaming.
     – Use "Exit" to close the app (it also stops the tail process).

  3. System Tray:
     – Close the window to hide it to the tray.
     – Right-click the tray icon to Show or Exit.

Troubleshooting:
  – If you see "Error: 'gcloud' command not found", ensure you have the
    Google Cloud SDK installed and "gcloud" is in your PATH.
  – Check permissions: your user must have permission to view App Engine
    logs in the specified project.
  – Consult the rotating log file (gcloud_tray_logger.log) for raw output.

Advanced:
  • You can configure log file size and backups in the script constants.
  • Modify the tray icon by editing create_icon_image() in gcloud_tray_logger.py

For questions, contributions, or issues, please refer to the project repository.
'''

def show_manual(parent=None):
    """
    Opens a manual window as a Tkinter Toplevel displaying the manual text.
    If parent is provided, the manual window is transient to it.
    """
    window = tk.Toplevel(parent) if parent else tk.Tk()
    window.title("GCloud Tray Logger Manual")
    window.geometry("600x500")

    txt = scrolledtext.ScrolledText(window, wrap=tk.WORD)
    txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    txt.insert(tk.END, MANUAL_TEXT)
    txt.config(state=tk.DISABLED)

    # If it’s a child window, don’t block the mainloop
    if parent:
        window.transient(parent)
        window.grab_set()
    else:
        window.mainloop()

if __name__ == '__main__':
    show_manual()
