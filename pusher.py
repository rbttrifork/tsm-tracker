"""Push local TSM data to the cloud-hosted dashboard.

Run this on your local machine on a schedule (e.g., Windows Task Scheduler every 30 min).
It reads AppData.lua, parses the current snapshot, and POSTs it to the cloud API.

Setup:
  1. Set environment variables:
     - TSM_PUSH_API_KEY=<your-secret-key>  (same key as on the cloud host)
     - TSM_CLOUD_URL=https://your-app.railway.app
  2. Run: python pusher.py
  3. Or schedule with Windows Task Scheduler to run every 30 minutes.
"""

import sys
import time
import requests
from config import APPDATA_LUA_PATH, REALM, TBC_ITEMS, PUSH_API_KEY, CLOUD_URL
from tsm_parser import parse_appdata_file, extract_prices


def push_snapshot():
    """Read local AppData.lua and push the snapshot to the cloud."""
    if not CLOUD_URL:
        print("ERROR: TSM_CLOUD_URL environment variable not set.")
        print("  Set it to your cloud dashboard URL, e.g.: https://your-app.railway.app")
        sys.exit(1)

    if not PUSH_API_KEY:
        print("ERROR: TSM_PUSH_API_KEY environment variable not set.")
        print("  Set it to the same secret key configured on your cloud host.")
        sys.exit(1)

    tracked_ids = set(TBC_ITEMS.keys())

    print(f"Reading {APPDATA_LUA_PATH}...")
    try:
        parsed = parse_appdata_file(APPDATA_LUA_PATH)
    except FileNotFoundError:
        print(f"ERROR: AppData.lua not found at {APPDATA_LUA_PATH}")
        print("  Make sure WoW/TSM has been run recently.")
        sys.exit(1)

    prices = extract_prices(parsed, realm=REALM)

    if not prices["downloadTime"]:
        print("ERROR: No download time found in AppData.lua")
        sys.exit(1)

    snapshot_time = prices["downloadTime"]
    print(f"Snapshot time: {snapshot_time} ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(snapshot_time))})")

    # Build price payload
    price_list = []
    for item_id, pdata in prices["items"].items():
        if item_id in tracked_ids:
            price_list.append({
                "item_id": item_id,
                "min_buyout": pdata.get("minBuyout"),
                "market_value": pdata.get("marketValue"),
                "market_value_recent": pdata.get("marketValueRecent"),
                "historical": pdata.get("historical"),
                "num_auctions": pdata.get("numAuctions"),
            })

    if not price_list:
        print("No tracked items found in current data.")
        return

    payload = {
        "snapshot_time": snapshot_time,
        "prices": price_list,
    }

    # Push to cloud
    url = f"{CLOUD_URL.rstrip('/')}/api/push"
    print(f"Pushing {len(price_list)} items to {url}...")

    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {PUSH_API_KEY}"},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        print(f"Success: {result.get('prices_received', 0)} prices received by cloud.")
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to {url}")
        print("  Check that TSM_CLOUD_URL is correct and the cloud app is running.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Server returned {resp.status_code}: {resp.text}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    push_snapshot()
