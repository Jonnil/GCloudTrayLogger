#!/usr/bin/env python3
import subprocess
import logging
import platform

def tail_logs(project_id: str, out_queue, stop_event):
    """
    1) Run `gcloud --version` (via pwsh on Windows, directly elsewhere)
       and emit its output.
    2) Then spawn `gcloud app logs tail --project=<project_id>` the same way,
       streaming lines into out_queue until stop_event is set.
    """
    logger = logging.getLogger("GCloudTrayLogger")
    is_windows = platform.system() == "Windows"

    # ── Step 1: gcloud version ────────────────────────────────
    if is_windows:
        version_cmd = [
            "pwsh", "-NoLogo", "-NoProfile", "-NonInteractive",
            "-Command", "gcloud --version"
        ]
    else:
        version_cmd = ["gcloud", "--version"]

    try:
        version_proc = subprocess.run(
            version_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        version_info = version_proc.stdout.strip()
        logger.info("gcloud version:\n%s", version_info)
        out_queue.put(f"gcloud version:\n{version_info}\n")
    except FileNotFoundError:
        msg = (
            "Error: could not find the gcloud CLI.\n"
            "Please install Google Cloud SDK and ensure 'gcloud' is on your PATH.\n"
        )
        logger.warning(msg.strip())
        out_queue.put(msg)
        return
    except subprocess.CalledProcessError as e:
        logger.warning("Failed to run gcloud --version: %s", e)
        out_queue.put(f"Warning: could not get gcloud version ({e})\n")

    # ── Step 2: begin tailing ──────────────────────────────────
    out_queue.put("Waiting for new log entries...\n")

    if is_windows:
        tail_cmd = [
            "pwsh", "-NoLogo", "-NoProfile", "-NonInteractive",
            "-Command", f"gcloud app logs tail --project={project_id}"
        ]
    else:
        tail_cmd = ["gcloud", "app", "logs", "tail", f"--project={project_id}"]

    logger.info("Starting log tail for project: %s", project_id)
    try:
        proc = subprocess.Popen(
            tail_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
    except FileNotFoundError:
        out_queue.put(
            "Error: 'gcloud' command not found on PATH.\n"
            "Please install the Google Cloud SDK.\n"
        )
        return
    except Exception as e:
        out_queue.put(f"Error launching log tail: {e}\n")
        return

    for line in proc.stdout:
        if stop_event.is_set():
            break
        logger.info(line.strip())
        out_queue.put(line)
    proc.stdout.close()
    proc.wait()
    logger.info("Log tail process exited")
    out_queue.put("-- Logging stopped --\n")
