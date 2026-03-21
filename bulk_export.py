"""One-off bulk export: push all local price snapshots and trades to the cloud."""

import sys
import requests
from db import get_db
from config import PUSH_API_KEY, CLOUD_URL

BATCH_SIZE = 500


def bulk_export():
    if not CLOUD_URL:
        print("ERROR: TSM_CLOUD_URL not set.")
        sys.exit(1)
    if not PUSH_API_KEY:
        print("ERROR: TSM_PUSH_API_KEY not set.")
        sys.exit(1)

    conn = get_db()

    # Read all snapshots grouped by snapshot_time
    snapshots = conn.execute(
        "SELECT item_id, snapshot_time, min_buyout, market_value, market_value_recent, historical, num_auctions "
        "FROM price_snapshots ORDER BY snapshot_time"
    ).fetchall()

    # Read all trades
    trades = conn.execute(
        "SELECT item_id, trade_type, stack_size, quantity, price_per_item, other_player, player, trade_time, source "
        "FROM trades ORDER BY trade_time"
    ).fetchall()
    conn.close()

    print(f"Local DB: {len(snapshots)} snapshots, {len(trades)} trades")

    # Group snapshots by snapshot_time
    time_groups = {}
    for row in snapshots:
        t = row["snapshot_time"]
        if t not in time_groups:
            time_groups[t] = []
        time_groups[t].append({
            "item_id": row["item_id"],
            "min_buyout": row["min_buyout"],
            "market_value": row["market_value"],
            "market_value_recent": row["market_value_recent"],
            "historical": row["historical"],
            "num_auctions": row["num_auctions"],
        })

    url = f"{CLOUD_URL.rstrip('/')}/api/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PUSH_API_KEY}",
    }

    # Push each snapshot time as a separate request
    total_prices = 0
    for snapshot_time, prices in sorted(time_groups.items()):
        payload = {
            "snapshot_time": snapshot_time,
            "prices": prices,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        total_prices += result["prices_received"]
        print(f"  Pushed {result['prices_received']} prices for time {snapshot_time}")

    # Push trades in batches (attached to a dummy snapshot_time since trades have their own timestamps)
    total_trades = 0
    for i in range(0, len(trades), BATCH_SIZE):
        batch = trades[i:i + BATCH_SIZE]
        trade_list = []
        for row in batch:
            trade_list.append({
                "item_id": row["item_id"],
                "trade_type": row["trade_type"],
                "stack_size": row["stack_size"],
                "quantity": row["quantity"],
                "price_per_item": row["price_per_item"],
                "other_player": row["other_player"],
                "player": row["player"],
                "trade_time": row["trade_time"],
                "source": row["source"],
            })

        # Use the first trade's time as a dummy snapshot_time, with an empty price list
        # We need at least one price for the endpoint, so send a minimal one
        payload = {
            "snapshot_time": batch[0]["trade_time"],
            "prices": [{"item_id": batch[0]["item_id"], "min_buyout": 0}],
            "trades": trade_list,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        total_trades += result["trades_received"]
        print(f"  Pushed {result['trades_received']} trades (batch {i // BATCH_SIZE + 1})")

    print(f"\nDone! Pushed {total_prices} prices + {total_trades} trades to {CLOUD_URL}")


if __name__ == "__main__":
    bulk_export()
