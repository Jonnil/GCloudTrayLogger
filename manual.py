#!/usr/bin/env python3
"""
GCloud Tray Logger Manual
Provides a simple GUI window displaying usage instructions and help for the GCloud Tray Logger.
"""
import tkinter as tk
from tkinter import scrolledtext

MANUAL_TEXT = '''
GCloud Tray Logger Manual
=========================

Overview
--------
GCloud Tray Logger is a Python GUI application that tails your
Google Cloud App Engine logs locally, writes them to rotating files,
and provides convenient system‐tray integration.

Installation & Launch
---------------------
1. Make sure you have Python 3.8–3.13 installed.
2. Install dependencies:
     pip install google-auth pystray pillow
3. Run the app:
     python main.py
   — or place a shortcut in your OS startup folder if you’ve enabled
     “Launch at system startup.”

Main Window
-----------
• **Project ID**  
  Enter your GCP project identifier (e.g. 'my-project-12345').  
  • Tip: hover for guidance or click **Open Cloud Settings** to go
    directly to IAM & Admin → Settings in the Cloud Console.

• **Install gcloud SDK**  
  If you haven’t installed Google Cloud SDK or ‘gcloud’ is not on your PATH,
  click here to install via Homebrew, Chocolatey, or apt-get.

• **Log File Path**  
  Choose where to store the local log file. Click **Browse…**
  to pick a different file or directory.

• **Daily log files**  
  When checked, a new file is created each day under `…/logs/YYYY-MM/`
  named `gcloud_tray_logger-YYYY-MM-DD.log`.

• **Launch at system startup**  
  When checked, the app will auto-start next time you log in.

• **Start minimized to tray**  
  When checked, the window will hide to the system tray immediately on launch.

• **Start Logging** / **Stop Logging**  
  Begin or end streaming of `gcloud app logs tail --project=<Project ID>`.
  Live output appears in the scrollable pane below.

• **Log Output Panel**  
  Shows live log lines. Right-click or use the **File** menu to:
    – **Clear Log Panel** (Ctrl+L)  
    – **Open Log File…** (Ctrl+O)  
    – **Export Logs…** (Ctrl+E)

System Tray
-----------
• Closing or minimizing the window hides it to the tray.
• Right-click the tray icon for:
    – **Show**  
    – **Exit**  

Menu Bar
--------
Under **File** you’ll find:
  • Session > Start/Stop/Clear  
  • Log Files > Open/Export  
  • Settings & Tools > Preferences (opens integrated settings)  
  • Exit (Ctrl+Q)

Help
----
• **Help > Manual** (F1) opens this window.

Troubleshooting
---------------
• **Error: 'gcloud' command not found**  
  Ensure you have the Google Cloud SDK installed and on your PATH,
  or click **Install gcloud SDK** in the main window.

• **Permissions errors**  
  Make sure your account can view App Engine logs on the specified project.

• **Log files**  
  Check the rotating files under your configured `logs` directory
  for raw output.

Feedback & Contribution
-----------------------
For issues, feature requests, or contributions, please visit the
project repository on GitHub.
'''

def show_manual(parent=None):
    """
    Opens a manual window displaying the updated GCloud Tray Logger Manual.
    """
    window = tk.Toplevel(parent) if parent else tk.Tk()
    window.title("GCloud Tray Logger Manual")
    window.geometry("650x550")

    txt = scrolledtext.ScrolledText(window, wrap=tk.WORD)
    txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    txt.insert(tk.END, MANUAL_TEXT)
    txt.config(state=tk.DISABLED)

    if parent:
        window.transient(parent)
        window.grab_set()
    else:
        window.mainloop()

if __name__ == '__main__':
    show_manual()
