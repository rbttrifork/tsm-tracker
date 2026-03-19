"""Parse TSM AppData.lua files and decode base-32 encoded auction data.

TSM uses Lua's tonumber(val, 32) for decoding, which uses digits 0-9 then A-V
(case-insensitive). For values longer than 6 characters, TSM splits them:
  tonumber(last6, 32) + tonumber(rest, 32) * 2^30
"""

import re

# Lua base-32 character set: 0-9, a-v (case insensitive)
B32_CHARS = "0123456789abcdefghijklmnopqrstuv"


def tsm_decode(s):
    """Decode a TSM base-32 encoded string to an integer.

    Mirrors TSM's Lua logic:
      if #val > 6 then
        val = tonumber(sub(val, -6), 32) + tonumber(sub(val, 1, -7), 32) * 2^30
      else
        val = tonumber(val, 32)
      end
    """
    if not s:
        return 0
    s = s.strip()
    if not s:
        return 0
    if len(s) > 6:
        tail = _b32_decode(s[-6:])
        head = _b32_decode(s[:-6])
        return tail + head * (2 ** 30)
    else:
        return _b32_decode(s)


def _b32_decode(s):
    """Decode a base-32 string (up to 6 chars) using Lua's character set."""
    result = 0
    for ch in s.lower():
        idx = B32_CHARS.index(ch)
        result = result * 32 + idx
    return result


def copper_to_gold(copper):
    """Convert copper amount to a dict with gold, silver, copper."""
    if copper is None:
        return None
    gold = copper // 10000
    silver = (copper % 10000) // 100
    cop = copper % 100
    return {"gold": gold, "silver": silver, "copper": cop, "total_copper": copper}


def copper_to_gold_float(copper):
    """Convert copper to a float in gold (e.g., 12345 copper -> 1.2345g)."""
    if copper is None:
        return None
    return copper / 10000.0


def parse_appdata_lua(content):
    """Parse a TSM AppData.lua or AppHelper.lua file content.

    Returns a dict with keys like:
    {
        'AUCTIONDB_NON_COMMODITY_DATA': {
            'realm': 'Spineshatter-Horde',
            'downloadTime': 1773866318,
            'fields': ['itemString', 'minBuyout', 'numAuctions', 'marketValueRecent'],
            'data': {item_id: {field: value, ...}, ...}
        },
        'AUCTIONDB_NON_COMMODITY_HISTORICAL': { ... },
        ...
    }
    """
    results = {}

    # Match each LoadData call
    # Pattern: LoadData("TYPE","REALM",[[return {downloadTime=N,fields={...},data={...}}]])
    pattern = r'LoadData\("([^"]+)","([^"]+)",\[\[return \{(.+?)\}\]\]\)'

    for match in re.finditer(pattern, content):
        data_type = match.group(1)
        realm = match.group(2)
        inner = match.group(3)

        # Extract downloadTime
        dt_match = re.search(r'downloadTime=(\d+)', inner)
        download_time = int(dt_match.group(1)) if dt_match else None

        # Extract fields
        fields_match = re.search(r'fields=\{([^}]+)\}', inner)
        if not fields_match:
            continue
        fields = [f.strip('"') for f in fields_match.group(1).split(",")]

        # Extract data entries: each is {val1,val2,val3,...}
        data_match = re.search(r'data=\{(.+)\}', inner)
        if not data_match:
            continue

        data_str = data_match.group(1)
        items = {}

        # Parse each {item_id, val1, val2, ...} entry
        for entry_match in re.finditer(r'\{([^}]+)\}', data_str):
            parts = entry_match.group(1).split(",")
            if len(parts) < 2:
                continue

            # First field is always itemString (the item ID as a plain integer)
            try:
                item_id = int(parts[0])
            except ValueError:
                continue

            item_data = {"itemString": item_id}

            # Parse remaining fields (base-32 encoded)
            for i, field_name in enumerate(fields[1:], 1):
                if i < len(parts):
                    raw = parts[i].strip()
                    if raw:
                        item_data[field_name] = tsm_decode(raw)
                    else:
                        item_data[field_name] = None

            items[item_id] = item_data

        results[data_type] = {
            "realm": realm,
            "downloadTime": download_time,
            "fields": fields,
            "data": items,
        }

    return results


def parse_appdata_file(filepath):
    """Parse a TSM AppData.lua file from disk."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_appdata_lua(content)


def extract_prices(parsed_data, realm="Spineshatter-Horde"):
    """Extract a unified price dict from parsed AppData.

    Returns: {
        'downloadTime': int,
        'items': {
            item_id: {
                'minBuyout': int (copper),
                'marketValueRecent': int (copper),
                'marketValue': int (copper),  # dbmarket
                'historical': int (copper),
                'numAuctions': int,
            }, ...
        }
    }
    """
    result = {"downloadTime": None, "items": {}}

    def ensure_item(item_id):
        if item_id not in result["items"]:
            result["items"][item_id] = {
                "minBuyout": None,
                "marketValueRecent": None,
                "marketValue": None,
                "historical": None,
                "numAuctions": None,
            }
        return result["items"][item_id]

    # Get current market data (minBuyout, numAuctions, marketValueRecent)
    commodity_data = parsed_data.get("AUCTIONDB_NON_COMMODITY_DATA")
    if commodity_data and commodity_data.get("realm") == realm:
        result["downloadTime"] = commodity_data["downloadTime"]
        for item_id, item_data in commodity_data["data"].items():
            entry = ensure_item(item_id)
            entry["minBuyout"] = item_data.get("minBuyout")
            entry["marketValueRecent"] = item_data.get("marketValueRecent")
            entry["numAuctions"] = item_data.get("numAuctions")

    # Merge scan stat data (marketValue = dbmarket)
    scan_stat = parsed_data.get("AUCTIONDB_NON_COMMODITY_SCAN_STAT")
    if scan_stat and scan_stat.get("realm") == realm:
        if result["downloadTime"] is None:
            result["downloadTime"] = scan_stat["downloadTime"]
        for item_id, item_data in scan_stat["data"].items():
            entry = ensure_item(item_id)
            entry["marketValue"] = item_data.get("marketValue")

    # Merge historical data
    historical_data = parsed_data.get("AUCTIONDB_NON_COMMODITY_HISTORICAL")
    if historical_data and historical_data.get("realm") == realm:
        if result["downloadTime"] is None:
            result["downloadTime"] = historical_data["downloadTime"]
        for item_id, item_data in historical_data["data"].items():
            entry = ensure_item(item_id)
            entry["historical"] = item_data.get("historical")

    return result


if __name__ == "__main__":
    # Quick test
    from config import APPDATA_LUA_PATH, TBC_ITEMS

    parsed = parse_appdata_file(APPDATA_LUA_PATH)
    prices = extract_prices(parsed)

    print(f"Download time: {prices['downloadTime']}")
    print(f"Total items parsed: {len(prices['items'])}")
    print(f"\nTracked TBC items found:")
    print(f"{'Item':<35} {'MinBuyout':>12} {'DBMarket':>12} {'Historical':>12} {'Auctions':>8}")
    print("-" * 82)

    for item_id, (name, category) in sorted(TBC_ITEMS.items(), key=lambda x: x[1][1]):
        if item_id in prices["items"]:
            p = prices["items"][item_id]
            mb = copper_to_gold_float(p["minBuyout"])
            mv = copper_to_gold_float(p["marketValue"])
            hist = copper_to_gold_float(p["historical"])
            na = p.get("numAuctions", 0) or 0
            mb_str = f"{mb:.2f}g" if mb else "N/A"
            mv_str = f"{mv:.2f}g" if mv else "N/A"
            hist_str = f"{hist:.2f}g" if hist else "N/A"
            print(f"{name:<35} {mb_str:>12} {mv_str:>12} {hist_str:>12} {na:>8}")
