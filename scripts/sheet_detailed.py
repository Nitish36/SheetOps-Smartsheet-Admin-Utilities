import requests
import urllib3
import time
from flask import session
from database import SessionLocal
from models.usage import UsageLog
from scripts.smartsheet_utils import fetch_smartsheet_inventory, update_progress, log_activity
urllib3.disable_warnings()



# --- Main Logic ---

def get_detailed_sheets(base_url, headers):
    """
    Step 1: Get high-level list of all sheets
    Step 2: Loop through every sheet to get detailed metadata
    """
    user_id = session.get("user_id")
    all_sheets_summary = fetch_smartsheet_inventory(base_url, headers, "sheets")

    final_results = []
    # --- PHASE 2: Get Detailed Metadata ---
    total_sheets = len(all_sheets_summary)
    update_progress(f"Step 2/2: Extracting details for {total_sheets} sheets...")

    for index, sheet in enumerate(all_sheets_summary):
        sheet_id = sheet.get("id")
        sheet_name = sheet.get("name")

        # Calculate progress percentage every 10 sheets to avoid spamming session
        if index % 10 == 0:
            update_progress(f"Processing {index}/{total_sheets}: {sheet_name}")

        try:
            # We use specific params to get Owner, Source, and Workspace info
            # pageSize=0 ensures we don't download the rows (faster)
            detail_url = f"{base_url}/{sheet_id}"
            params = {
                "include": "owner,source,workspace",
                "pageSize": 0
            }

            # 1. API Call
            res = requests.get(detail_url, headers=headers, params=params, verify=False)

            # 2. Log Activity (Logs every single sheet detail fetch)
            log_activity(user_id, detail_url, "GET")

            if res.status_code != 200:
                print(f"⚠️ Could not access sheet: {sheet_id}")
                continue

            detail = res.json()

            # 3. Map the Data (Exactly as requested)
            final_results.append({
                "id": detail.get("id"),
                "accesslevel": detail.get("accessLevel"),
                "createdAt": detail.get("createdAt"),
                "dependenciesEnabled": detail.get("dependenciesEnabled"),
                "ganttEnabled": detail.get("ganttEnabled"),
                "hasSummaryFields": detail.get("hasSummaryFields"),
                "name": detail.get("name"),
                "owner": detail.get("owner"),
                "permalink": detail.get("permalink"),
                "source.type": detail.get("source", {}).get("type") if detail.get("source") else None,
                "totalRowCount": detail.get("totalRowCount"),
                "userPermissions.summaryPermissions": detail.get("userPermissions", {}).get("summaryPermissions"),
                "version": detail.get("version"),
                "workspace.name": detail.get("workspace", {}).get("name") if detail.get("workspace") else None,
                "workspace.accessLevel": detail.get("workspace", {}).get("accessLevel") if detail.get(
                    "workspace") else None
            })

            # Small sleep to prevent rate limiting
            time.sleep(0.1)

        except Exception as e:
            print(f"❌ Error on sheet {sheet_id}: {e}")
            # Optional: update_progress(f"Error fetching {sheet_name}")

    update_progress("Detailed extraction completed")
    update_progress("✅ Export ready")

    return final_results