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

def get_trial_dashboard(url, headers):
    all_dashboards = []
    page = 1
    page_size = 50   # ✅ max allowed
    user_id = session.get("user_id")  # ------>
    update_progress("Fetching sheets (trial mode)")
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

        all_dashboards.extend(batch)
        update_progress(f"Fetched {len(all_dashboards)} sheets so far")

        print(f"Fetched page {page} | Total Dashboards so far: {len(all_dashboards)}")

        if len(all_dashboards) >= 50:
            update_progress("Trial limit reached (50 rows)")
            all_dashboards = all_dashboards[:50]
            break

        page += 1
        time.sleep(1)  # ⏱ polite to API
    update_progress("Sheets extraction completed")
    update_progress("✅ Export completed")

    return all_dashboards
