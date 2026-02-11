import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import pandas as pd
import time
import os
import urllib3
urllib3.disable_warnings()


class SmartsheetSheetExtractor:
    def __init__(self, token):
        self.base_url = "https://api.smartsheet.com/2.0"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "smartsheet-integration-source": "AI,SampleOrg,Report-Exporter-v1"
        }
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def get_all_sheets_list(self):
        """Step 1: Get the high-level list of all sheets"""
        sheets = []
        page = 1
        while True:
            # We use the /sheets endpoint to get the inventory
            response = self.session.get(f"{self.base_url}/sheets", headers=self.headers,
                                        params={"page": page, "pageSize": 200}, verify=False)
            response.raise_for_status()
            data = response.json()
            print(data)
            sheets.extend(data.get("data", []))
            if page >= data.get("totalPages", 0): break
            page += 1
        return sheets

    def extract_sheet_details(self):
        """Step 2: Get detailed metadata for each sheet"""
        raw_sheets = self.get_all_sheets_list()
        print(raw_sheets)
        final_results = []

        print(f"📋 Found {len(raw_sheets)} sheets. Fetching enterprise metadata...")

        for s in raw_sheets:
            sheet_id = s.get("id")
            try:
                # include=owner,source handles those specific fields
                # pageSize=0 ensures we DON'T download rows (making it much faster)
                params = {
                    "include": "owner,source,workspace",
                    "pageSize": 0
                }
                res = self.session.get(f"{self.base_url}/sheets/{sheet_id}", headers=self.headers, params=params)

                if res.status_code != 200:
                    print(f"⚠️ Could not access sheet: {sheet_id}")
                    continue

                detail = res.json()

                # Mapping the data to your specific column requirements
                final_results.append({
                    "id": detail.get("id"),
                    "accesslevel": detail.get("accessLevel"),
                    "createdAt": detail.get("createdAt"),
                    "dependenciesEnabled": detail.get("dependenciesEnabled"),
                    "ganttEnabled": detail.get("ganttEnabled"),
                    "hasSummaryFields": detail.get("hasSummaryFields"),
                    "name": detail.get("name"),
                    "owner": detail.get("owner"),  # This is usually the owner's email
                    "permalink": detail.get("permalink"),
                    "source.type": detail.get("source", {}).get("type") if detail.get("source") else None,
                    "totalRowCount": detail.get("totalRowCount"),
                    "userPermissions.summaryPermissions": detail.get("userPermissions", {}).get("summaryPermissions"),
                    "version": detail.get("version"),
                    "workspace.name": detail.get("workspace", {}).get("name") if detail.get("workspace") else None,
                    "workspace.accessLevel": detail.get("workspace", {}).get("accessLevel") if detail.get(
                        "workspace") else None
                })

                # Small sleep to prevent aggressive API hitting
                time.sleep(0.1)

            except Exception as e:
                print(f"❌ Error on sheet {sheet_id}: {e}")

        return pd.DataFrame(final_results)


# --- EXECUTION ---
TOKEN = "Token"
extractor = SmartsheetSheetExtractor(TOKEN)
df_sheets = extractor.extract_sheet_details()

# Export to CSV
#os.makedirs("exports", exist_ok=True)
df_sheets.to_csv("sheets/Sheets_Detailed_Metadata.csv", index=False)

print(f"\n🎉 Success! Exported {len(df_sheets)} sheets to CSV.")