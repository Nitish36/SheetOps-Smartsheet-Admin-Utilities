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

def get_trial_sheets(url, headers):
    all_sheets = []
    page = 1
    page_size = 50
    user_id = session.get("user_id")    # ------>
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

        all_sheets.extend(batch)
        update_progress(f"Fetched {len(all_sheets)} sheets so far")

        if len(all_sheets) >= 50:
            update_progress("Trial limit reached (50 rows)")
            all_sheets = all_sheets[:50]
            break

        page += 1
        time.sleep(1)
    update_progress("Sheets extraction completed")
    update_progress("✅ Export completed")

    return all_sheets
