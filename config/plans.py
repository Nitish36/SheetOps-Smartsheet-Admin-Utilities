# config/tiers.py

TIER_CONFIG = {
    "trial": {
        "max_rows": 50,
        "allow_deep_scrape": False,
        "script_folder": "trial_scripts"
    },
    "paid": {
        "max_rows": None,
        "allow_deep_scrape": False,
        "script_folder": "scripts"
    },
    "enterprise": {
        "max_rows": None,
        "allow_deep_scrape": True,
        "script_folder": "enterprise_scripts"
    }
}
