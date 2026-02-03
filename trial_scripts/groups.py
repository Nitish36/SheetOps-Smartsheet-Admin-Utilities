import requests
import urllib3
import pandas as pd
import time

urllib3.disable_warnings()

# -------------------------------------------------
# Paginated fetch (groups only)
# -------------------------------------------------
def safe_get(url, headers, params=None, retries=3, sleep_sec=2):
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url,
                headers=headers,
                params=params,
                verify=False,
                timeout=30
            )
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(sleep_sec)
            else:
                return None

def get_all_trial_groups(base_url, headers):
    all_groups = []
    page = 1
    page_size = 50

    while True:
        params = {"page": page, "pageSize": page_size}
        resp = safe_get(f"{base_url}", headers, params)

        if not resp:
            break

        data = resp.json()
        batch = data.get("data", [])

        if not batch:
            break

        all_groups.extend(batch)

        print(f"Fetched groups page {page} | Total: {len(all_groups)}")

        if len(all_groups)>=50:
            all_groups=all_groups[:50]
            break

        page += 1
        time.sleep(1)

    return all_groups

def get_trial_group_members(base_url, headers, groups):
    rows = []
    skipped = []

    for group in groups:
        group_id = group["id"]
        group_name = group["name"]
        owner = group.get("owner", "")

        resp = safe_get(f"{base_url}/{group_id}", headers)

        if not resp:
            skipped.append(group_name)
            continue

        members = resp.json().get("members", [])

        for m in members:
            access = m.get("accessLevel", {})
            rows.append({
                "group_name": group_name,
                "owner": owner,
                "name": m.get("name", ""),
                "email": m.get("email", ""),
                "resource_viewer": access.get("resourceViewer", False),
                "group_admin": access.get("groupAdmin", False),
                "system_admin": access.get("systemAdmin", False),
                "jira_admin": access.get("jiraAdmin", False),
            })

    return rows, skipped

def build_trial_group_dataframe(rows):
    df = pd.DataFrame(rows)
    return df
