"""Import trade history from TSM SavedVariables backup zips and current files.

The TSM backup zips contain SavedVariables (not AppData.lua AuctionDB data).
We extract csvBuys and csvSales which contain actual auction house transaction
history with timestamps and prices — useful for understanding price patterns.
"""

import os
import re
import zipfile
import glob
import time
from config import BACKUP_DIR, BACKUP_ACCOUNT_PREFIX, REALM, TBC_ITEMS, APPDATA_LUA_PATH
from tsm_parser import parse_appdata_file, extract_prices
from db import init_db, populate_items, insert_trades_bulk, insert_price_snapshots_bulk


def parse_item_string(item_str):
    """Parse TSM item string like 'i:22456' to item_id 22456."""
    m = re.match(r"i:(\d+)", item_str)
    return int(m.group(1)) if m else None


def extract_csv_trades(content, realm_key="Spineshatter"):
    """Extract csvBuys and csvSales from TradeSkillMaster.lua SavedVariables content.

    Returns list of (item_id, trade_type, stack_size, quantity, price_per_item, other_player, player, trade_time, source)
    """
    trades = []

    for trade_type, csv_key in [("sell", "csvSales"), ("buy", "csvBuys")]:
        pattern = rf'\["r@{realm_key}@internalData@{csv_key}"\]\s*=\s*"(.*?)"'
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            continue

        raw = m.group(1)
        # Lines are separated by literal \n in the lua string
        lines = raw.split("\\n")

        for line in lines:
            # Skip header
            if line.startswith("itemString,") or not line.strip():
                continue

            parts = line.split(",")
            # Format: itemString,stackSize,quantity,price,otherPlayer,player,time,source
            if len(parts) < 8:
                continue

            item_id = parse_item_string(parts[0])
            if item_id is None:
                continue

            try:
                stack_size = int(parts[1])
                quantity = int(parts[2])
                price = int(parts[3])  # total price in copper
                other_player = parts[4]
                player = parts[5]
                trade_time = int(parts[6])
                source = parts[7]
            except (ValueError, IndexError):
                continue

            # Only include Auction trades (skip Vendor)
            if source != "Auction":
                continue

            # Calculate price per item
            price_per_item = price  # TSM stores price per item already

            trades.append((
                item_id, trade_type, stack_size, quantity,
                price_per_item, other_player, player, trade_time, source
            ))

    return trades


def list_backup_files():
    """List all relevant backup zip files, sorted by timestamp."""
    pattern = os.path.join(BACKUP_DIR, f"{BACKUP_ACCOUNT_PREFIX}*.zip")
    files = glob.glob(pattern)

    def get_ts(f):
        base = os.path.basename(f)
        ts_str = base.replace(BACKUP_ACCOUNT_PREFIX, "").replace(".zip", "")
        try:
            return int(ts_str)
        except ValueError:
            return 0

    files.sort(key=get_ts)
    return files


def import_trades_from_zip(zip_path):
    """Extract trade history from a backup zip."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            tsm_name = None
            for name in zf.namelist():
                if name == "TradeSkillMaster.lua":
                    tsm_name = name
                    break

            if not tsm_name:
                return []

            content = zf.read(tsm_name).decode("utf-8", errors="replace")
            return extract_csv_trades(content)
    except (zipfile.BadZipFile, KeyError, UnicodeDecodeError) as e:
        print(f"  Error reading {os.path.basename(zip_path)}: {e}")
        return []


def import_trades_from_current_savedvariables():
    """Import trades from the current SavedVariables file on disk."""
    sv_path = os.path.join(
        os.path.dirname(APPDATA_LUA_PATH),
        "..", "..", "..", "WTF", "Account", "KENTHSOLEM",
        "SavedVariables", "TradeSkillMaster.lua"
    )
    sv_path = os.path.normpath(sv_path)

    if not os.path.exists(sv_path):
        print(f"SavedVariables not found at {sv_path}")
        return []

    print(f"Reading current SavedVariables: {sv_path}")
    with open(sv_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    return extract_csv_trades(content)


def import_all():
    """Import trade history from backups and current SavedVariables, plus current price snapshot."""
    init_db()
    populate_items(TBC_ITEMS)
    tracked_ids = set(TBC_ITEMS.keys())

    # --- 1. Import trade history from the most recent backup (has cumulative data) ---
    backup_files = list_backup_files()
    print(f"Found {len(backup_files)} backup files")

    all_trades = []

    if backup_files:
        # The most recent backup has the most complete trade history
        latest_backup = backup_files[-1]
        print(f"Extracting trade history from latest backup: {os.path.basename(latest_backup)}")
        all_trades = import_trades_from_zip(latest_backup)

    # Also try current SavedVariables (may have newer trades)
    current_trades = import_trades_from_current_savedvariables()
    if current_trades:
        all_trades.extend(current_trades)

    # Filter to tracked items and deduplicate
    tracked_trades = [t for t in all_trades if t[0] in tracked_ids]
    print(f"Found {len(all_trades)} total auction trades, {len(tracked_trades)} for tracked items")

    if tracked_trades:
        insert_trades_bulk(tracked_trades)
        print(f"Inserted trade records into database")

    # --- 2. Collect current price snapshot from AppData.lua ---
    print(f"\nCollecting current price snapshot from AppData.lua...")
    parsed = parse_appdata_file(APPDATA_LUA_PATH)
    prices = extract_prices(parsed)

    if prices["downloadTime"] and prices["items"]:
        rows = []
        dt = prices["downloadTime"]
        for item_id, pdata in prices["items"].items():
            if item_id in tracked_ids:
                rows.append((
                    item_id, dt,
                    pdata.get("minBuyout"),
                    pdata.get("marketValue"),
                    pdata.get("marketValueRecent"),
                    pdata.get("historical"),
                    pdata.get("numAuctions"),
                ))
        if rows:
            insert_price_snapshots_bulk(rows)
            print(f"Inserted {len(rows)} price snapshot records")
            print(f"Snapshot time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(dt))}")

    # --- Summary ---
    from db import get_db
    conn = get_db()
    trade_count = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    snapshot_count = conn.execute("SELECT COUNT(*) FROM price_snapshots").fetchone()[0]
    trade_range = conn.execute("SELECT MIN(trade_time), MAX(trade_time) FROM trades").fetchone()
    conn.close()

    print(f"\n=== Import Summary ===")
    print(f"Total trades in DB: {trade_count}")
    print(f"Total price snapshots in DB: {snapshot_count}")
    if trade_range[0]:
        earliest = time.strftime('%Y-%m-%d', time.localtime(trade_range[0]))
        latest = time.strftime('%Y-%m-%d', time.localtime(trade_range[1]))
        print(f"Trade history range: {earliest} to {latest}")


if __name__ == "__main__":
    start = time.time()
    import_all()
    elapsed = time.time() - start
    print(f"\nCompleted in {elapsed:.1f}s")
