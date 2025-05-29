# GCloud Tray Logger

A cross-platform Python GUI for tailing Google Cloud App Engine logs locally, with rotating files, per-day logs, system tray integration, and a one-click Cloud SDK installer.

## Features

- Real-time log tailing  
- Rotating log files (size-based) or daily files under `logs/YYYY-MM/`  
- System tray minimize/restore (Send to Tray button)  
- Built-in installer for Google Cloud SDK  
- Configurable project ID & log path  
- Persistent status/info bar  

## Install

**From source:**

    git clone https://github.com/Jonnil/GCloudTrayLogger.git
    cd GCloudTrayLogger
    pip install -r requirements.txt

## Usage

Run the application:

    python main.py

1. Enter your **GCP Project ID**  
2. (Optional) Click **Install gcloud SDK**  
3. Configure your log path and daily-log toggle  
4. Click **Start Logging**  
5. Minimize with **Send to Tray**; restore from the tray icon  