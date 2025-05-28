import subprocess
import logging

def tail_logs(project_id: str, out_queue, stop_event):
    """
    Spawn `gcloud --version`, log its output, then
    `gcloud app logs tail --project=…` and stream lines into out_queue.
    """
    logger = logging.getLogger("GCloudTrayLogger")

    # 1) Log the gcloud version
    version_cmd = [
        "pwsh", "-NoLogo", "-NoProfile", "-NonInteractive", 
        "-Command", "gcloud --version"
    ]
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
    except subprocess.CalledProcessError as e:
        logger.warning("Failed to run gcloud --version: %s", e)
        out_queue.put(f"Warning: could not get gcloud version ({e})\n")
    except FileNotFoundError:
        out_queue.put(
            "Error: PowerShell or gcloud not found on PATH.\n"
            "Please install gcloud SDK and ensure pwsh+gcloud are available.\n"
        )
        return

    # 2) Indicate we’re about to start tailing
    out_queue.put("Waiting for new log entries...\n")

    # 3) Tail the logs
    tail_cmd = [
        "pwsh", "-NoLogo", "-NoProfile", "-NonInteractive",
        "-Command", f"gcloud app logs tail --project={project_id}"
    ]
    logger.info("Starting log tail for project: %s", project_id)
    try:
        proc = subprocess.Popen(
            tail_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
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
