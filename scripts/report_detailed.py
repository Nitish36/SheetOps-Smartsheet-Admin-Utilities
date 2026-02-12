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

def get_detailed_reports(base_url, headers):
    """
    Step 1: Get list of all reports
    Step 2: Get details for each report
    Step 3: Flatten 'Source Sheets' and 'Scope' into a single row structure
    """
    all_reports_summary = []
    final_data = []

    user_id = session.get("user_id")
    page = 1
    page_size = 100

    # --- PHASE 1: Get the Inventory ---
    update_progress("Step 1/2: Fetching report inventory...")

    while True:
        params = {
            "page": page,
            "pageSize": page_size
        }

        # 1. API Call
        response = requests.get(base_url, headers=headers, params=params, verify=False)

        # 2. Log Activity
        log_activity(user_id, base_url, "GET")

        response.raise_for_status()
        data = response.json()
        batch = data.get("data", [])

        if not batch:
            break

        all_reports_summary.extend(batch)
        update_progress(f"Found {len(all_reports_summary)} reports so far...")

        if page >= data.get("totalPages", 0):
            break

        page += 1
        time.sleep(0.2)

    # --- PHASE 2: Get Detailed Metadata & Flatten ---
    total_reports = len(all_reports_summary)
    update_progress(f"Step 2/2: Extracting details for {total_reports} reports...")

    for index, rep in enumerate(all_reports_summary):
        report_id = rep.get("id")
        report_name = rep.get("name")

        if index % 5 == 0:
            update_progress(f"Processing {index}/{total_reports}: {report_name}")

        try:
            url = f"{base_url}/{report_id}"
            # include="workspace" ensures the parent workspace name isn't null
            # pageSize=0 ensures we don't load the actual report rows (too heavy)
            params = {"pageSize": 0, "include": "workspace"}

            # 1. API Call
            response = requests.get(url, headers=headers, params=params, verify=False)

            # 2. Log Activity
            log_activity(user_id, url, "GET")

            if response.status_code != 200:
                print(f"⚠️ Failed for report: {report_name}")
                continue

            detail = response.json()

            # --- FLATTENING LOGIC (Preserved from your script) ---
            scope_sheets = detail.get("scope", {}).get("sheets", [])
            scope_workspaces = detail.get("scope", {}).get("workspaces", [])
            source_sheets = detail.get("sourceSheets", [])
            parent_workspace = detail.get("workspace", {})

            # Base metadata
            row_base = {
                "isSummaryReport": detail.get("isSummaryReport"),
                "accessLevel": detail.get("accessLevel"),
                "createdAt": detail.get("createdAt"),
                "dependenciesEnabled": detail.get("dependenciesEnabled"),
                "ganttEnabled": detail.get("ganttEnabled"),
                "hasSummaryFields": detail.get("hasSummaryFields"),
                "modifiedAt": detail.get("modifiedAt"),
                "name": detail.get("name"),
                "totalRowCount": detail.get("totalRowCount"),
                "workspace.name": parent_workspace.get("name") if parent_workspace else None,
                "workspace.accessLevel": parent_workspace.get("accessLevel") if parent_workspace else None,
                "scope.workspaces[].id": scope_workspaces[0].get("id") if scope_workspaces else None,
                "scope.workspaces[].name": scope_workspaces[0].get("name") if scope_workspaces else None,
                "scope.workspaces[].accessLevel": scope_workspaces[0].get("accessLevel") if scope_workspaces else None,
                "scope.workspaces[].permalink": scope_workspaces[0].get("permalink") if scope_workspaces else None,
            }

            # If multiple source sheets, create a row for each
            if source_sheets:
                for i, ss in enumerate(source_sheets):
                    row = row_base.copy()
                    # Add Source Sheet Info
                    row["sourceSheets[].id"] = ss.get("id")
                    row["sourceSheets[].accessLevel"] = ss.get("accessLevel")
                    row["sourceSheets[].createdAt"] = ss.get("createdAt")
                    row["sourceSheets[].ganttEnabled"] = ss.get("ganttEnabled")
                    row["sourceSheets[].hasSummaryFields"] = ss.get("hasSummaryFields")
                    row["sourceSheets[].modifiedAt"] = ss.get("modifiedAt")
                    row["sourceSheets[].name"] = ss.get("name")
                    row["sourceSheets[].owner"] = ss.get("owner")
                    row["sourceSheets[].permalink"] = ss.get("permalink")
                    row["sourceSheets[].readOnly"] = ss.get("readOnly")
                    row["sourceSheets[].totalRowCount"] = ss.get("totalRowCount")
                    row["sourceSheets[].userPermissions.summaryPermissions"] = ss.get("userPermissions", {}).get(
                        "summaryPermissions")

                    # Add Matching Scope Sheet Info (if exists)
                    if i < len(scope_sheets):
                        sc = scope_sheets[i]
                        row["scope.sheets[].id"] = sc.get("id")
                        row["scope.sheets[].accessLevel"] = sc.get("accessLevel")
                        row["scope.sheets[].createdAt"] = sc.get("createdAt")
                        row["scope.sheets[].name"] = sc.get("name")
                        row["scope.sheets[].owner"] = sc.get("owner")
                        row["scope.sheets[].permalink"] = sc.get("permalink")
                        row["scope.sheets[].source.type"] = sc.get("source", {}).get("type") if sc.get(
                            "source") else None
                        row["scope.sheets[].totalRowCount"] = sc.get("totalRowCount")

                    final_data.append(row)
            else:
                # No source sheets, just add base row
                final_data.append(row_base)

            time.sleep(0.1)

        except Exception as e:
            print(f"❌ Error processing {report_name}: {e}")

    update_progress("Detailed report extraction completed")
    update_progress("✅ Export ready")

    return final_data