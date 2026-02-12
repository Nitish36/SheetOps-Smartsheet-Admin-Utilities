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

def get_detailed_dashboards(base_url, headers):
    """
    Step 1: Get list of all dashboards (sights)
    Step 2: Get details for each dashboard (widgets, layout, etc.)
    Step 3: Flatten into rows (One row per Widget)
    """
    all_dashboards_summary = []
    final_data = []

    user_id = session.get("user_id")
    page = 1
    page_size = 100

    # --- PHASE 1: Get the Inventory ---
    update_progress("Step 1/2: Fetching dashboard inventory...")

    while True:
        params = {
            "page": page,
            "pageSize": page_size
        }

        # 1. API Call (List Dashboards)
        response = requests.get(base_url, headers=headers, params=params, verify=False)

        # 2. Log Activity
        log_activity(user_id, base_url, "GET")

        response.raise_for_status()
        data = response.json()
        batch = data.get("data", [])

        if not batch:
            break

        all_dashboards_summary.extend(batch)
        update_progress(f"Found {len(all_dashboards_summary)} dashboards so far...")

        if page >= data.get("totalPages", 0):
            break

        page += 1
        time.sleep(0.2)

    # --- PHASE 2: Get Detailed Metadata & Flatten ---
    total_dashboards = len(all_dashboards_summary)
    update_progress(f"Step 2/2: Extracting details for {total_dashboards} dashboards...")

    for index, dash in enumerate(all_dashboards_summary):
        sight_id = dash.get("id")
        name = dash.get("name")

        if index % 5 == 0:
            update_progress(f"Processing {index}/{total_dashboards}: {name}")

        try:
            url = f"{base_url}/{sight_id}"
            # include=source handles the source.id/type fields
            # level=2 or 4 ensures we get widget data
            params = {"include": "source", "level": 4}

            # 1. API Call
            response = requests.get(url, headers=headers, params=params, verify=False)

            # 2. Log Activity
            log_activity(user_id, url, "GET")

            if response.status_code != 200:
                print(f"⚠️ Failed to fetch details for: {name}")
                continue

            detail = response.json()
            widgets = detail.get("widgets", [])

            # Helper to get workspace info safely
            workspace = detail.get("workspace", {})

            # Base metadata for the dashboard
            row_base = {
                "ID": detail.get("id"),
                "name": detail.get("name"),
                "accessLevel": detail.get("accessLevel"),
                "columnCount": detail.get("columnCount"),
                "backgroundColor": detail.get("backgroundColor"),
                "defaultWidgetBackgroundColor": detail.get("defaultWidgetBackgroundColor"),
                "permalink": detail.get("permalink"),
                # Source info
                "source.id": detail.get("source", {}).get("id") if detail.get("source") else None,
                "source.type": detail.get("source", {}).get("type") if detail.get("source") else None,
                # Workspace info
                "workspace.id": workspace.get("id") if workspace else None,
                "workspace.name": workspace.get("name") if workspace else None,
                "createdAt": detail.get("createdAt"),
                "Modified At": detail.get("modifiedAt")
            }

            # If there are widgets, create a row for each widget
            if widgets:
                for w in widgets:
                    row = row_base.copy()
                    row["widget.id"] = w.get("id")
                    row["widget.type"] = w.get("type")
                    # You can add more widget details here if needed (contents, title, etc)
                    final_data.append(row)
            else:
                # If no widgets, add one row with empty widget info so the dashboard still appears in report
                row = row_base.copy()
                row["widget.id"] = None
                row["widget.type"] = None
                final_data.append(row)

            time.sleep(0.1)

        except Exception as e:
            print(f"❌ Error processing {name}: {e}")

    update_progress("Detailed dashboard extraction completed")
    update_progress("✅ Export ready")

    return final_data