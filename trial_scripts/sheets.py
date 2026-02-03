import requests
import urllib3
import time

urllib3.disable_warnings()

def get_trial_sheets(url, headers):
    all_sheets = []
    page = 1
    page_size = 50

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

        if len(all_sheets) >= 50:
            all_sheets = all_sheets[:50]
            break

        page += 1
        time.sleep(1)

    return all_sheets
