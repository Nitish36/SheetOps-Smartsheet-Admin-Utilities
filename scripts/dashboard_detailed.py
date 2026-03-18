import requests
import urllib3
import time
from flask import session
# Note: Removed SessionLocal and UsageLog imports as they are handled in smartsheet_utils
from scripts.smartsheet_utils import fetch_smartsheet_inventory, update_progress, log_activity

urllib3.disable_warnings()


def get_detailed_dashboards(base_url, headers):
    """
    Step 1: Get list of all dashboards (sights)
    Step 2: Get details for each dashboard (widgets, layout, etc.)
    Step 3: Flatten into rows (One row per Widget)
    """
    # 1. Fetch the inventory (Sights)
    # Changed label to "dashboards" for the progress bar
    all_dashboards_summary = fetch_smartsheet_inventory(base_url, headers, "dashboards")

    final_data = []
    user_id = session.get("user_id")

    # 2. Define the total count for the progress bar
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
            # level=4 ensures we get widget data
            params = {"include": "source", "level": 4}

            # API Call
            response = requests.get(url, headers=headers, params=params, verify=False)

            # Log Activity
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
                "source.id": detail.get("source", {}).get("id") if detail.get("source") else None,
                "source.type": detail.get("source", {}).get("type") if detail.get("source") else None,
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
                    final_data.append(row)
            else:
                # If no widgets, add one row with empty widget info
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