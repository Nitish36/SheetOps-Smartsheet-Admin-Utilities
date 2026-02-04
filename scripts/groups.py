import requests
import urllib3
import pandas as pd
import time
from flask import session
urllib3.disable_warnings()

def update_progress(message):
    progress = session.get("progress", [])
    progress.append(message)
    session["progress"] = progress

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

def get_all_groups(base_url, headers):
    all_groups = []
    page = 1
    page_size = 200
    update_progress("Fetching Groups (pro/enterprise mode)")
    while True:
        update_progress(f"Requesting page {page}")
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

        page += 1
        time.sleep(1)
    update_progress("Groups extraction completed")
    update_progress("✅ Export completed")

    return all_groups

def get_group_members(base_url, headers, groups):
    rows = []
    skipped = []

    for group in groups:
        group_id = group["id"]
        group_name = group["name"]
        owner = group.get("owner", "")

        resp = safe_get(f"{base_url}/groups/{group_id}", headers)

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

def build_group_dataframe(rows):
    df = pd.DataFrame(rows)
    return df
