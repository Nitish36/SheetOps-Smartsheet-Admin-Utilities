import requests
import urllib3
import pandas as pd
import time
import os

urllib3.disable_warnings()

BASE_URL = "https://api.smartsheet.com/2.0"
TOKEN = "XWxWMt3Gat2RiR6GOUrLfRgymt59kpDnj05A1"  # Replace with your actual token

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "smartsheet-integration-source": "AI,SampleOrg,My-AI-Connector-v2"
}

# -----------------------------
# STEP 1: LIST ALL DASHBOARDS
# -----------------------------
all_dashboards = []
page = 1
page_size = 200

print("📊 Fetching dashboard list...")

while True:
    params = {"page": page, "pageSize": page_size}
    response = requests.get(f"{BASE_URL}/sights", headers=HEADERS, params=params, verify=False)
    response.raise_for_status()

    data = response.json()
    batch = data.get("data", [])
    if not batch:
        break

    all_dashboards.extend(batch)
    if page >= data.get("totalPages", 0):
        break
    page += 1

print(f"✅ Found {len(all_dashboards)} dashboards. Fetching details...")

# -----------------------------
# STEP 2: GET DETAILS & FLATTEN
# -----------------------------
final_data = []

for dash in all_dashboards:
    sight_id = dash.get("id")
    name = dash.get("name")

    # Fetch detailed dashboard object
    # include=source handles the source.id/type fields
    # level=4 ensures we get the most up-to-date widget data
    url = f"{BASE_URL}/sights/{sight_id}"
    params = {"include": "source", "level": 4}

    try:
        response = requests.get(url, headers=HEADERS, params=params, verify=False)
        if response.status_code != 200:
            print(f"⚠️ Failed to fetch details for: {name}")
            continue

        detail = response.json()
        widgets = detail.get("widgets", [])

        # Prepare dashboard-level metadata
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
            "workspace.id": detail.get("workspace", {}).get("id") if detail.get("workspace") else None,
            "workspace.name": detail.get("workspace", {}).get("name") if detail.get("workspace") else None,
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

        print(f"✔ Processed: {name}")
        time.sleep(0.2)  # Avoid hitting rate limits

    except Exception as e:
        print(f"❌ Error processing {name}: {e}")

# -----------------------------
# STEP 3: EXPORT TO CSV
# -----------------------------
if final_data:
    df_final = pd.DataFrame(final_data)

    # Reorder columns to match your exact request
    column_order = [
        "ID", "name", "accessLevel", "columnCount", "backgroundColor",
        "defaultWidgetBackgroundColor", "permalink", "source.id", "source.type",
        "widget.id", "widget.type", "workspace.id", "workspace.name",
        "createdAt", "Modified At"
    ]
    df_final = df_final[column_order]

    os.makedirs("dashboard", exist_ok=True)
    df_final.to_csv("dashboard/Dashboard_Detailed_List.csv", index=False)
    print(f"\n🎉 Success! Exported {len(df_final)} rows to 'dashboard/Dashboard_Detailed_List.csv'")
else:
    print("\n⚠️ No data found to export.")