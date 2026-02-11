import requests
import urllib3
import time
from flask import session

urllib3.disable_warnings()


def update_progress(message):
    progress = session.get("progress", [])
    progress.append(message)
    session["progress"] = progress
    session.modified = True


def get_trial_contact(url, headers):
    all_contacts = []
    page = 1
    page_size = 100

    while True:
        params = {"page": page, "pageSize": page_size}
        response = requests.get(url, headers=headers, params=params, verify=False)

        if response.status_code != 200:
            break

        data = response.json()
        batch = data.get("data", [])

        if not batch:
            break

        all_contacts.extend(batch)

        # Stop at 50 for Trial
        if len(all_contacts) >= 50:
            all_contacts = all_contacts[:50]
            break

        if page >= data.get("totalPages", 1):
            break

        page += 1
        time.sleep(0.1)

    update_progress("Contact extraction completed")
    return all_contacts