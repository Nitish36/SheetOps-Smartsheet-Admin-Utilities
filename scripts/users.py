import requests
import urllib3

urllib3.disable_warnings()

def get_users(url, headers):
    all_users = []
    page = 1
    page_size = 300  # max allowed by Smartsheet

    while True:
        params = {
            "page": page,
            "pageSize": page_size
        }

        resp = requests.get(url, headers=headers, params=params, verify=False)
        resp.raise_for_status()

        data = resp.json()
        users = data.get("data", [])

        all_users.extend(users)

        print(f"✅ Fetched page {page} | Users: {len(users)}")

        # stop when last page is reached
        if len(users) < page_size:
            break

        page += 1

    return all_users
