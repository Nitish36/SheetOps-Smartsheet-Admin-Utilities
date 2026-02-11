import requests
import urllib3
import time
from flask import session

urllib3.disable_warnings()


def update_progress(message):
    """Updates the session progress list for the UI"""
    progress = session.get("progress", [])
    progress.append(message)
    session["progress"] = progress
    session.modified = True


def get_pro_contact(url, headers):
    """
    Fetches ALL contacts for Pro/Enterprise users.
    URL should be the full endpoint: https://api.smartsheet.com/2.0/contacts
    """
    all_contacts = []
    page = 1
    page_size = 100

    update_progress("🔍 Starting full contact extraction...")

    while True:
        params = {"page": page, "pageSize": page_size}
        response = requests.get(url, headers=headers, params=params, verify=False)

        if response.status_code != 200:
            print(f"Error fetching contacts: {response.text}")
            break

        data = response.json()
        batch = data.get("data", [])

        if not batch:
            break

        # Flatten the data to only include id, name, and email
        for c in batch:
            all_contacts.append({
                "id": c.get("id"),
                "name": c.get("name"),
                "email": c.get("email")
            })

        # Check if we have more pages
        total_pages = data.get("totalPages", 1)
        update_progress(f"Reading page {page} of {total_pages}...")

        if page >= total_pages:
            break

        page += 1
        time.sleep(0.1)  # Respect rate limits

    update_progress(f"✅ Extraction completed. Found {len(all_contacts)} contacts.")
    return all_contacts