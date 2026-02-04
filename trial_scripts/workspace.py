import requests
import urllib3
import time
from flask import session
urllib3.disable_warnings()

def update_progress(message):
    progress = session.get("progress", [])
    progress.append(message)
    session["progress"] = progress

def get_trial_workspace(url, headers):
    all_workspaces = []
    page = 1
    page_size = 50   # ✅ max allowed
    update_progress("Fetching sheets (trial mode)")
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
        update_progress(f"Fetched {len(all_workspaces)} sheets so far")

        print(f"Fetched page {page} | Total sheets so far: {len(all_workspaces)}")

        if len(all_workspaces) >= 50:
            update_progress("Trial limit reached (50 rows)")
            all_workspaces = all_workspaces[:50]
            break

        page += 1
        time.sleep(1)  # ⏱ polite to API

    update_progress("Sheets extraction completed")
    update_progress("✅ Export completed")

    return all_workspaces
