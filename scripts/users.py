import requests
import urllib3
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

def get_users(url, headers):
    all_users = []
    page = 1
    page_size = 300  # max allowed by Smartsheet
    user_id = session.get("user_id")  # ------>
    update_progress("Fetching sheets (trial mode)")
    while True:
        update_progress(f"Requesting page {page}")
        params = {
            "page": page,
            "pageSize": page_size
        }

        resp = requests.get(url, headers=headers, params=params, verify=False)
        try:                                            # ------>
            log_activity(user_id, url, "GET")
        except Exception as e:
            print(f"Logging failed: {e}")
        resp.raise_for_status()

        data = resp.json()
        users = data.get("data", [])

        all_users.extend(users)
        update_progress(f"Fetched {len(users)} sheets so far")
        print(f"✅ Fetched page {page} | Users: {len(users)}")

        # stop when last page is reached
        if len(users) < page_size:
            break

        page += 1
    update_progress("Users extraction completed")
    update_progress("✅ Export completed")
    return all_users
