import requests
import urllib3
import pandas as pd
import time
from flask import session
urllib3.disable_warnings()

def update_progress(message):
    progress = session.get("progress", [])
    progress.append(message)
    session["progress"] = progress

def get_workspace(url, headers):
    all_workspaces = []
    page = 1
    page_size = 200   # ✅ max allowed
    update_progress("Fetching workspaces (pro/enterprise mode)")
    while True:
        params = {
            "page": page,
            "pageSize": page_size
        }

        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()

        data = response.json()
        batch = data.get("data", [])

        if not batch:
            update_progress("No more data returned from API")
            break

        all_workspaces.extend(batch)

        print(f"Fetched page {page} | Total sheets so far: {len(all_workspaces)}")

        if page >= data.get("totalPages", 0):
            break

        page += 1
        time.sleep(1)  # ⏱ polite to API
    update_progress("Workspace extraction completed")
    update_progress("✅ Export completed")
    return all_workspaces
