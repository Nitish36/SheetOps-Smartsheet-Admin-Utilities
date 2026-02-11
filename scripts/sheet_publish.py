import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import pandas as pd
import time
import os
import urllib3

urllib3.disable_warnings()


class SmartsheetPublishExtractor:
    def __init__(self, token):
        self.base_url = "https://api.smartsheet.com/2.0"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "smartsheet-integration-source": "YourAppName_PublishAudit_v1"
        }
        self.session = requests.Session()
        # Retry strategy for rate limiting (429) and server errors
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def get_sheets_inventory(self):
        """Fetches the list of all sheets to get their IDs"""
        sheets = []
        page = 1
        while True:
            response = self.session.get(f"{self.base_url}/sheets", headers=self.headers,
                                        params={"page": page, "pageSize": 100}, verify=False)
            response.raise_for_status()
            data = response.json()
            sheets.extend(data.get("data", []))
            if page >= data.get("totalPages", 0): break
            page += 1
        return sheets

    def extract_publish_data(self, test_mode=True):
        """Fetches publish status for each sheet and flattens it for CSV"""
        all_sheets = self.get_sheets_inventory()

        # --- TEST MODE LIMITER ---
        if test_mode:
            print(f"🧪 TEST MODE: Processing only first 5 sheets out of {len(all_sheets)} found.")
            all_sheets = all_sheets[:5]
        else:
            print(f"📊 Processing all {len(all_sheets)} sheets...")

        final_results = []

        for s in all_sheets:
            sheet_id = s.get("id")
            sheet_name = s.get("name")

            try:
                # API Endpoint: GET /sheets/{sheetId}/publish
                res = self.session.get(f"{self.base_url}/sheets/{sheet_id}/publish", headers=self.headers, verify=False)

                if res.status_code != 200:
                    print(f"⚠️ Could not fetch publish status for: {sheet_name}")
                    continue

                pub = res.json()

                # Map the response to your requested columns
                final_results.append({
                    "sheet_id": sheet_id,
                    "sheet_name": sheet_name,
                    "icalUrl": pub.get("icalUrl"),
                    "readOnlyFullUrl": pub.get("readOnlyFullUrl"),
                    "readOnlyLiteSslUrl": pub.get("readOnlyLiteSslUrl"),
                    "readOnlyLiteUrl": pub.get("readOnlyLiteUrl"),
                    "readWriteUrl": pub.get("readWriteUrl"),
                    "icalEnabled": pub.get("icalEnabled"),
                    "readOnlyFullAccessibleBy": pub.get("readOnlyFullAccessibleBy"),
                    "readOnlyFullDefaultView": pub.get("readOnlyFullDefaultView"),
                    "readOnlyFullEnabled": pub.get("readOnlyFullEnabled"),
                    "readOnlyLiteEnabled": pub.get("readOnlyLiteEnabled"),
                    "readWriteAccessibleBy": pub.get("readWriteAccessibleBy"),
                    "readWriteDefaultView": pub.get("readWriteDefaultView"),
                    "readWriteEnabled": pub.get("readWriteEnabled")
                })

                print(f"✔ Fetched: {sheet_name}")
                time.sleep(0.2)  # Conservative pace for rate limits

            except Exception as e:
                print(f"❌ Error on sheet {sheet_name}: {e}")

        return pd.DataFrame(final_results)


# --- EXECUTION ---
TOKEN = "Token"  # Replace with your token
extractor = SmartsheetPublishExtractor(TOKEN)

# Set test_mode=False when you are ready to run for the whole account
df_publish = extractor.extract_publish_data(test_mode=True)

# -----------------------------
# EXPORT TO CSV
# -----------------------------
if not df_publish.empty:
    # Ensure specific column order as requested
    column_order = [
        "sheet_id", "sheet_name", "icalUrl", "readOnlyFullUrl", "readOnlyLiteSslUrl",
        "readOnlyLiteUrl", "readWriteUrl", "icalEnabled", "readOnlyFullAccessibleBy",
        "readOnlyFullDefaultView", "readOnlyFullEnabled", "readOnlyLiteEnabled",
        "readWriteAccessibleBy", "readWriteDefaultView", "readWriteEnabled"
    ]

    # Add columns if they are missing in the API response (e.g. if nothing is published)
    for col in column_order:
        if col not in df_publish.columns:
            df_publish[col] = None

    df_publish = df_publish[column_order]

    #os.makedirs("exports", exist_ok=True)
    df_publish.to_csv("sheets/Sheets_Publish_Status.csv", index=False)
    print(f"\n🎉 Success! Exported to 'exports/Sheets_Publish_Status.csv'")
else:
    print("\n⚠️ No data found.")