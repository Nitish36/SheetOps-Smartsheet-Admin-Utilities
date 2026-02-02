import requests
import urllib3
import pandas as pd
import time

urllib3.disable_warnings()

def get_webhooks(url,headers):
    all_webhooks = []
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

        all_webhooks.extend(batch)

        print(f"Fetched page {page} | Total sheets so far: {len(all_webhooks)}")

        if 50 >= data.get("totalPages", 0):
            break

        page += 1
        time.sleep(1)  # ⏱ polite to API
        return all_webhooks
