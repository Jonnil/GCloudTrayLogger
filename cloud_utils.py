import webbrowser

def open_cloud_settings(project_id: str, infobar):
    """
    Opens the IAM & Admin Settings page in the browser.
    If project_id is blank or placeholder, opens generic page.
    """
    if not project_id or project_id == "your-project-id":
        url = "https://console.cloud.google.com/iam-admin/settings"
        infobar.set_message(
            "Opening IAM & Admin Settings… please select a project in the console."
        )
    else:
        url = f"https://console.cloud.google.com/iam-admin/settings?project={project_id}"
        infobar.set_message(f"Opening settings for project: {project_id}")

    try:
        webbrowser.open(url)
    except Exception as e:
        infobar.set_message(f"Error opening browser: {e}")
