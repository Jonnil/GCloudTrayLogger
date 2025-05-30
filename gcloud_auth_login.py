#!/usr/bin/env python3
"""
gcloud_auth_login.py

Helper to run `gcloud auth login` in a background thread,
streaming output and status back via callbacks, and then
automatically set the active project.
"""

import subprocess
import threading

def gcloud_auth_login(project_id: str, *, output_callback, status_callback):
    """
    1) Launches an interactive `gcloud auth login`.
    2) If that succeeds, runs `gcloud config set project PROJECT_ID`.

    :param project_id:       the GCP project to set after login
    :param output_callback:  fn(str) – called for each line of process output.
    :param status_callback:  fn(str) – called to update non-modal status messages.
    """
    def _worker():
        # Step 1: authenticate
        status_callback("Starting gcloud authentication…")
        auth_cmd = ["gcloud", "auth", "login", "--brief"]
        try:
            proc = subprocess.Popen(
                auth_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=False
            )
        except FileNotFoundError:
            err = "Error: 'gcloud' not found on PATH. Please install the Google Cloud SDK.\n"
            output_callback(err)
            status_callback("Authentication failed")
            return

        for line in proc.stdout:
            output_callback(line)
        proc.stdout.close()
        code = proc.wait()

        if code != 0:
            status_callback(f"Auth exited with code {code}")
            output_callback(f">>> gcloud auth login exited with code {code}\n")
            return

        # success!
        status_callback("Authentication succeeded")
        output_callback("✔ gcloud auth login completed successfully.\n")

        # Step 2: set the project
        if project_id:
            status_callback(f"Setting project → {project_id}…")
            cfg_cmd = ["gcloud", "config", "set", "project", project_id]
            try:
                cfg_proc = subprocess.Popen(
                    cfg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    shell=False
                )
            except FileNotFoundError:
                err = "Error: 'gcloud' not found on PATH during config set.\n"
                output_callback(err)
                status_callback("Failed to set project")
                return

            for line in cfg_proc.stdout:
                output_callback(line)
            cfg_proc.stdout.close()
            cfg_code = cfg_proc.wait()

            if cfg_code == 0:
                status_callback(f"Project set to {project_id}")
                output_callback(f"✔ gcloud config set project {project_id} completed.\n")
            else:
                status_callback(f"Config set exited {cfg_code}")
                output_callback(f">>> gcloud config set project exited with code {cfg_code}\n")
        else:
            output_callback("⚠️  No Project ID provided; skipping `gcloud config set project`.\n")
            status_callback("No project to set")

    threading.Thread(target=_worker, daemon=True).start()
