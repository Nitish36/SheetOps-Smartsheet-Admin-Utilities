# scripts/smartsheet_utils.py
import requests
import time
from flask import session
from database import SessionLocal
from models.usage import UsageLog


def log_activity(user_id, endpoint, method):
    try:
        db = SessionLocal()
        new_log = UsageLog(user_id=user_id, endpoint=endpoint, method=method)
        db.add(new_log)
        db.commit()
        db.close()
    except Exception as e:
        print(f"Logging failed: {e}")


def update_progress(message):
    progress = session.get("progress", [])
    progress.append(message)
    session["progress"] = progress


def fetch_smartsheet_inventory(base_url, headers, type_label):
    """
    Generic helper to fetch ALL items from any Smartsheet list endpoint.
    Works for Sheets, Reports, Dashboards, Workspaces, etc.
    """
    all_items = []
    page = 1
    user_id = session.get("user_id")

    update_progress(f"Step 1/2: Fetching {type_label} inventory...")

    while True:
        params = {"page": page, "pageSize": 100}

        # 1. API Call
        response = requests.get(base_url, headers=headers, params=params, verify=False)

        # 2. Log Activity
        log_activity(user_id, base_url, "GET")

        response.raise_for_status()
        data = response.json()
        batch = data.get("data", [])

        if not batch:
            break

        all_items.extend(batch)
        update_progress(f"Found {len(all_items)} {type_label} so far...")

        if page >= data.get("totalPages", 0):
            break

        page += 1
        time.sleep(0.2)

    return all_items