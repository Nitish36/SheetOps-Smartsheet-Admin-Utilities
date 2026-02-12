import requests
import urllib3
import time
from flask import session
from database import SessionLocal
from models.usage import UsageLog

urllib3.disable_warnings()


# --- Helper Functions ---

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


# --- Main Logic ---

def get_published_sheets(base_url, headers):
    """
    Step 1: Get high-level list of all sheets to get IDs
    Step 2: Loop through every sheet to get /publish status
    """
    all_sheets_summary = []
    final_results = []

    user_id = session.get("user_id")
    page = 1
    page_size = 200  # Max allowed by Smartsheet for listing

    # --- PHASE 1: Get the Inventory (List of IDs) ---
    update_progress("Step 1/2: Fetching sheet inventory...")

    while True:
        params = {
            "page": page,
            "pageSize": page_size
        }

        # 1. API Call (List Sheets)
        response = requests.get(base_url, headers=headers, params=params, verify=False)

        # 2. Log Activity
        log_activity(user_id, base_url, "GET")

        response.raise_for_status()
        data = response.json()
        batch = data.get("data", [])

        if not batch:
            break

        all_sheets_summary.extend(batch)
        update_progress(f"Found {len(all_sheets_summary)} sheets so far...")

        if page >= data.get("totalPages", 0):
            break

        page += 1
        time.sleep(0.2)

        # --- PHASE 2: Get Publish Status ---
    total_sheets = len(all_sheets_summary)
    update_progress(f"Step 2/2: Checking publish status for {total_sheets} sheets...")

    for index, sheet in enumerate(all_sheets_summary):
        sheet_id = sheet.get("id")
        sheet_name = sheet.get("name")

        # Update progress every 10 items
        if index % 10 == 0:
            update_progress(f"Scanning {index}/{total_sheets}: {sheet_name}")

        try:
            # Endpoint: /sheets/{id}/publish
            pub_url = f"{base_url}/{sheet_id}/publish"

            # 1. API Call
            res = requests.get(pub_url, headers=headers, verify=False)

            # 2. Log Activity
            log_activity(user_id, pub_url, "GET")

            if res.status_code != 200:
                # Some sheets might not support publishing or return 404 if deleted
                # We skip them but don't crash
                continue

            pub = res.json()

            # 3. Map the Data
            # We explicitly define keys to ensure the CSV has all columns even if data is missing
            final_results.append({
                "sheet_id": sheet_id,
                "sheet_name": sheet_name,
                "icalUrl": pub.get("icalUrl"),
                "readOnlyFullUrl": pub.get("readOnlyFullUrl"),
                "readOnlyLiteSslUrl": pub.get("readOnlyLiteSslUrl"),
                "readOnlyLiteUrl": pub.get("readOnlyLiteUrl"),
                "readWriteUrl": pub.get("readWriteUrl"),
                "icalEnabled": pub.get("icalEnabled"),
                "readOnlyFullAccessibleBy": pub.get("readOnlyFullAccessibleBy"),
                "readOnlyFullDefaultView": pub.get("readOnlyFullDefaultView"),
                "readOnlyFullEnabled": pub.get("readOnlyFullEnabled"),
                "readOnlyLiteEnabled": pub.get("readOnlyLiteEnabled"),
                "readWriteAccessibleBy": pub.get("readWriteAccessibleBy"),
                "readWriteDefaultView": pub.get("readWriteDefaultView"),
                "readWriteEnabled": pub.get("readWriteEnabled")
            })

            # Small sleep to prevent rate limiting
            time.sleep(0.1)

        except Exception as e:
            print(f"❌ Error on sheet {sheet_id}: {e}")
            # Optional: update_progress(f"Error fetching {sheet_name}")

    update_progress("Publish extraction completed")
    update_progress("✅ Export ready")

    return final_results