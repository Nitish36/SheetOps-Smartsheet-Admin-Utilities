import requests
import urllib3
import time
from flask import session
from database import SessionLocal
from models.usage import UsageLog
urllib3.disable_warnings()

def log_activity(user_id, endpoint, method):                       # ---->
    db = SessionLocal()
    new_log = UsageLog(user_id=user_id, endpoint=endpoint, method=method)
    db.add(new_log)
    db.commit()
    db.close()

def update_progress(message):
    progress = session.get("progress", [])
    progress.append(message)
    session["progress"] = progress

def get_trial_workspace(url, headers):
    all_workspaces = []
    page = 1
    page_size = 50   # ✅ max allowed
    user_id = session.get("user_id")  # ------>
    update_progress("Fetching workspaces (trial mode)")
    while True:
        update_progress(f"Requesting page {page}")
        params = {
            "page": page,
            "pageSize": page_size
        }

        response = requests.get(url, headers=headers, params=params, verify=False)
        try:                                            # ------>
            log_activity(user_id, url, "GET")
        except Exception as e:
            print(f"Logging failed: {e}")
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

    update_progress("Workspace extraction completed")
    update_progress("✅ Export completed")

    return all_workspaces
