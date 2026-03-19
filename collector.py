"""Collect a fresh price snapshot from the current AppData.lua into the database."""

import time
from config import APPDATA_LUA_PATH, REALM, TBC_ITEMS
from tsm_parser import parse_appdata_file, extract_prices
from db import init_db, populate_items, insert_price_snapshots_bulk


def collect_snapshot():
    """Read current AppData.lua and insert new price data into the database."""
    init_db()
    populate_items(TBC_ITEMS)

    tracked_ids = set(TBC_ITEMS.keys())

    print(f"Reading {APPDATA_LUA_PATH}...")
    parsed = parse_appdata_file(APPDATA_LUA_PATH)
    prices = extract_prices(parsed, realm=REALM)

    if not prices["downloadTime"]:
        print("ERROR: No download time found in AppData.lua")
        return 0

    dt = prices["downloadTime"]
    print(f"Snapshot time: {dt} ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(dt))})")

    rows = []
    for item_id, pdata in prices["items"].items():
        if item_id in tracked_ids:
            rows.append((
                item_id,
                dt,
                pdata.get("minBuyout"),
                pdata.get("marketValue"),
                pdata.get("marketValueRecent"),
                pdata.get("historical"),
                pdata.get("numAuctions"),
            ))

    if rows:
        insert_price_snapshots_bulk(rows)
        print(f"Inserted {len(rows)} price points for tracked items.")
    else:
        print("No tracked items found in current data.")

    return len(rows)


if __name__ == "__main__":
    collect_snapshot()
