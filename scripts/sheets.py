import requests
import urllib3
import time
from flask import session
urllib3.disable_warnings()

def update_progress(message):
    progress = session.get("progress", [])
    progress.append(message)
    session["progress"] = progress

def get_sheets(url, headers):
    all_sheets = []
    page = 1
    page_size = 200   # ✅ max allowed
    update_progress("Fetching sheets (pro/enterprise mode)")
    while True:
        params = {
            "page": page,
            "pageSize": page_size
        }

        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()

        data = response.json()
        batch = data.get("data", [])

        if not batch:
            break

        all_sheets.extend(batch)
        update_progress(f"Fetched {len(all_sheets)} sheets so far")
        print(f"Fetched page {page} | Total sheets so far: {len(all_sheets)}")

        if page >= data.get("totalPages", 0):
            break

        page += 1
        time.sleep(1)  # ⏱ polite to API
    update_progress("Sheets extraction completed")
    update_progress("✅ Export completed")
    return all_sheets