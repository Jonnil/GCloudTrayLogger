#!/usr/bin/env python3
"""
install_gcloud_sdk.py

Helper to install Chocolatey (on Windows) if needed,
then install the Google Cloud SDK on macOS, Windows, or Linux.
Runs the appropriate commands in a background thread,
and reports progress via callbacks.
"""

import sys
import platform
import subprocess
import threading
import shutil

CHOCOLATEY_INSTALL_PS = (
    "Set-ExecutionPolicy Bypass -Scope Process -Force;"
    "[System.Net.ServicePointManager]::SecurityProtocol = "
    "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072;"
    "iex ((New-Object System.Net.WebClient).DownloadString('"
    "https://community.chocolatey.org/install.ps1'"
    "))"
)

def install_gcloud_sdk(output_callback, status_callback=None):
    """
    Starts a background installation of:
      • Chocolatey (on Windows) if not already installed, then
      • Google Cloud SDK via the system package manager.

    Parameters:
      output_callback(str)    – called for each line of installer output.
      status_callback(str)    – called when installation starts, succeeds, or fails.

    Example usage in your GUI:
        install_gcloud_sdk(
            output_callback=lambda line: self._append_log(line),
            status_callback=lambda msg: self.infobar.set_message(msg)
        )
    """
    def _installer():
        is_mac = sys.platform.startswith("darwin")
        is_win = sys.platform.startswith("win")
        is_linux = not (is_mac or is_win)

        # 1) On Windows, ensure Chocolatey is present
        if is_win:
            if shutil.which("choco") is None:
                # Try to install Chocolatey via PowerShell
                if shutil.which("pwsh"):
                    pw = "pwsh"
                else:
                    pw = "powershell"

                status_callback and status_callback("Installing Chocolatey…")
                output_callback(">>> Bootstrapping Chocolatey via PowerShell…\n")

                try:
                    proc = subprocess.Popen(
                        [pw, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", CHOCOLATEY_INSTALL_PS],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                except Exception as e:
                    msg = f"Failed to launch PowerShell for Chocolatey install: {e}"
                    status_callback and status_callback(msg)
                    output_callback(msg + "\n")
                    return

                # Stream Chocolatey install output
                for line in proc.stdout:
                    output_callback(line)
                code = proc.wait()
                if code != 0:
                    msg = f"Chocolatey installer exited with code {code}"
                    status_callback and status_callback(msg)
                    output_callback(f">>> {msg}\n")
                    return

                # re-check for choco
                if shutil.which("choco") is None:
                    msg = (
                        "Chocolatey install appears to have failed.\n"
                        "Please install manually from https://chocolatey.org/install"
                    )
                    status_callback and status_callback(msg)
                    output_callback(msg + "\n")
                    return

        # 2) Install Google Cloud SDK
        if is_mac:
            cmd = ["brew", "install", "google-cloud-sdk"]
            shell = False
            start_msg = "Installing Google Cloud SDK via Homebrew…"
        elif is_win:
            cmd = ["choco", "install", "gcloudsdk", "-y"]
            shell = True
            start_msg = "Installing Google Cloud SDK via Chocolatey…"
        else:  # assume Debian-based Linux
            cmd = "sudo apt-get update && sudo apt-get install google-cloud-sdk -y"
            shell = True
            start_msg = "Installing Google Cloud SDK via apt-get…"

        status_callback and status_callback(start_msg)
        output_callback(f">>> Running installer: {cmd}\n")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=shell,
                text=True
            )
        except Exception as e:
            msg = f"Failed to start SDK installer: {e}"
            status_callback and status_callback(msg)
            output_callback(msg + "\n")
            return

        # Stream installer output
        for line in proc.stdout:
            output_callback(line)
        code = proc.wait()

        if code == 0:
            success = "Google Cloud SDK installed successfully!"
            status_callback and status_callback(success)
            output_callback(">>> Installation complete!\n")
        else:
            fail = f"SDK installer exited with code {code}"
            status_callback and status_callback(fail)
            output_callback(f">>> {fail}\n")

    threading.Thread(target=_installer, daemon=True).start()
