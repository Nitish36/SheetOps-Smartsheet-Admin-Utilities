import requests
import urllib3
import time
from flask import session
urllib3.disable_warnings()

def update_progress(message):
    progress = session.get("progress", [])
    progress.append(message)
    session["progress"] = progress

def get_trial_sheets(url, headers):
    all_sheets = []
    page = 1
    page_size = 50
    update_progress("Fetching sheets (trial mode)")
    while True:
        update_progress(f"Requesting page {page}")
        params = {
            "page": page,
            "pageSize": page_size
        }

        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()

        data = response.json()
        batch = data.get("data", [])

        if not batch:
            update_progress("No more data returned from API")
            break

        all_sheets.extend(batch)
        update_progress(f"Fetched {len(all_sheets)} sheets so far")

        if len(all_sheets) >= 50:
            update_progress("Trial limit reached (50 rows)")
            all_sheets = all_sheets[:50]
            break

        page += 1
        time.sleep(1)
    update_progress("Sheets extraction completed")
    update_progress("✅ Export completed")

    return all_sheets
