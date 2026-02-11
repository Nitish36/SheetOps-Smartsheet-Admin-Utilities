import requests
import urllib3
import pandas as pd
import time
import os

urllib3.disable_warnings()

# ==========================================
# CONFIGURATION & TEST MODE
# ==========================================
TOKEN = "Token"
BASE_URL = "https://api.smartsheet.com/2.0"
TEST_MODE = True  # Set to False to process ALL reports
TEST_LIMIT = 5  # Number of reports to process in Test Mode

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "smartsheet-integration-source": "AI,SampleOrg,Report-Exporter-v1"
}

# -----------------------------
# STEP 1: LIST ALL REPORTS
# -----------------------------
all_reports = []
page = 1
page_size = 100

print("📊 Fetching report list...")

while True:
    params = {"page": page, "pageSize": page_size}
    response = requests.get(f"{BASE_URL}/reports", headers=HEADERS, params=params, verify=False)
    response.raise_for_status()

    data = response.json()
    batch = data.get("data", [])
    if not batch:
        break

    all_reports.extend(batch)
    if page >= data.get("totalPages", 0):
        break
    page += 1

# Apply Test Mode Limiter
total_found = len(all_reports)
if TEST_MODE:
    all_reports = all_reports[:TEST_LIMIT]
    print(f"🧪 TEST MODE ENABLED: Processing first {len(all_reports)} reports out of {total_found} found.")
else:
    print(f"🚀 FULL MODE: Processing all {total_found} reports.")

# -----------------------------
# STEP 2: GET DETAILS & FLATTEN
# -----------------------------
final_data = []

for rep in all_reports:
    report_id = rep.get("id")
    report_name = rep.get("name")

    url = f"{BASE_URL}/reports/{report_id}"
    try:
        # include="workspace" ensures the parent workspace name isn't null
        params = {"pageSize": 0, "include": "workspace"}
        response = requests.get(url, headers=HEADERS, params=params, verify=False)

        if response.status_code != 200:
            print(f"⚠️ Failed for report: {report_name}")
            continue

        detail = response.json()

        # Extract Scope and Source lists
        scope_sheets = detail.get("scope", {}).get("sheets", [])
        scope_workspaces = detail.get("scope", {}).get("workspaces", [])
        source_sheets = detail.get("sourceSheets", [])
        parent_workspace = detail.get("workspace", {})

        # Base metadata for the report
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

        # If there are multiple source sheets, create a row for each
        if source_sheets:
            for i, ss in enumerate(source_sheets):
                row = row_base.copy()
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

                if i < len(scope_sheets):
                    sc = scope_sheets[i]
                    row["scope.sheets[].id"] = sc.get("id")
                    row["scope.sheets[].accessLevel"] = sc.get("accessLevel")
                    row["scope.sheets[].createdAt"] = sc.get("createdAt")
                    row["scope.sheets[].name"] = sc.get("name")
                    row["scope.sheets[].owner"] = sc.get("owner")
                    row["scope.sheets[].permalink"] = sc.get("permalink")
                    row["scope.sheets[].source.type"] = sc.get("source", {}).get("type") if sc.get("source") else None
                    row["scope.sheets[].totalRowCount"] = sc.get("totalRowCount")

                final_data.append(row)
        else:
            final_data.append(row_base)

        print(f"✔ Processed detail for: {report_name}")
        time.sleep(0.3)

    except Exception as e:
        print(f"❌ Error processing {report_name}: {e}")

# -----------------------------
# STEP 3: EXPORT TO CSV
# -----------------------------
if final_data:
    df_reports = pd.DataFrame(final_data)
    column_order = [
        "scope.sheets[].id", "scope.sheets[].accessLevel", "scope.sheets[].createdAt",
        "scope.sheets[].name", "scope.sheets[].owner", "scope.sheets[].permalink",
        "scope.sheets[].source.type", "scope.sheets[].totalRowCount",
        "scope.workspaces[].id", "scope.workspaces[].name", "scope.workspaces[].accessLevel",
        "scope.workspaces[].permalink",
        "sourceSheets[].id", "sourceSheets[].accessLevel", "sourceSheets[].createdAt",
        "sourceSheets[].ganttEnabled", "sourceSheets[].hasSummaryFields", "sourceSheets[].modifiedAt",
        "sourceSheets[].name", "sourceSheets[].owner", "sourceSheets[].permalink",
        "sourceSheets[].readOnly", "sourceSheets[].totalRowCount", "sourceSheets[].userPermissions.summaryPermissions",
        "isSummaryReport", "accessLevel", "createdAt", "dependenciesEnabled", "ganttEnabled",
        "hasSummaryFields", "modifiedAt", "name", "totalRowCount", "workspace.name", "workspace.accessLevel"
    ]

    for col in column_order:
        if col not in df_reports.columns:
            df_reports[col] = None

    df_reports = df_reports[column_order]

    #os.makedirs("reports", exist_ok=True)
    filename = "report/Report_Test_List.csv" if TEST_MODE else "reports/Report_Full_List.csv"
    df_reports.to_csv(filename, index=False)
    print(f"\n🎉 Success! Exported {len(df_reports)} rows to '{filename}'")
else:
    print("\n⚠️ No data found.")