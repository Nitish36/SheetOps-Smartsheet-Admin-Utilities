import requests
import urllib3
import time

urllib3.disable_warnings()


def get_trial_workspace(url, headers):
    all_workspaces = []
    page = 1
    page_size = 50   # ✅ max allowed

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

        all_workspaces.extend(batch)

        print(f"Fetched page {page} | Total sheets so far: {len(all_workspaces)}")

        if len(all_workspaces) >= 50:
            all_workspaces = all_workspaces[:50]
            break

        page += 1
        time.sleep(1)  # ⏱ polite to API
        return all_workspaces
