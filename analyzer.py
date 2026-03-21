"""Buy-low recommendation engine for TSM Price Tracker."""

import time
from db import get_db
from config import RAID_DAYS, BUY_LOW_THRESHOLD


def get_recommendations():
    """Analyze prices and return buy-low recommendations.

    Returns a list of dicts:
    [{
        'item_id': int,
        'name': str,
        'category': str,
        'current_min_buyout': int (copper),
        'avg_7d': float (copper),
        'avg_14d': float (copper),
        'avg_raid_day_price': float (copper),
        'avg_off_day_price': float (copper),
        'discount_pct': float,  # how much below average
        'expected_profit_pct': float,  # expected gain if sold on raid day
        'confidence': float,  # 0-1, how consistent the pattern is
        'signal': str,  # 'strong_buy', 'buy', 'hold'
        'num_auctions': int,
    }, ...]
    """
    conn = get_db()
    now = int(time.time())
    seven_days_ago = now - 7 * 86400
    fourteen_days_ago = now - 14 * 86400

    # Get all tracked items
    items = conn.execute("SELECT item_id, name, category FROM items").fetchall()
    recommendations = []

    for item in items:
        item_id = item["item_id"]

        # Get the latest snapshot — use minBuyout as the "buy now" price
        latest = conn.execute(
            """SELECT min_buyout, market_value, num_auctions, snapshot_time
               FROM price_snapshots
               WHERE item_id = ? AND min_buyout IS NOT NULL AND min_buyout > 0
               ORDER BY snapshot_time DESC LIMIT 1""",
            (item_id,),
        ).fetchone()

        if not latest:
            continue

        # Current buyable price is minBuyout; rolling averages use dbmarket
        current_price = latest["min_buyout"]
        current_auctions = latest["num_auctions"] or 0

        # 7-day average (prefer dbmarket, fall back to minBuyout)
        avg_7d_row = conn.execute(
            """SELECT AVG(COALESCE(market_value, min_buyout)) as avg_price, COUNT(*) as cnt
               FROM price_snapshots
               WHERE item_id = ? AND snapshot_time >= ? AND COALESCE(market_value, min_buyout) IS NOT NULL AND COALESCE(market_value, min_buyout) > 0""",
            (item_id, seven_days_ago),
        ).fetchone()

        # 14-day average
        avg_14d_row = conn.execute(
            """SELECT AVG(COALESCE(market_value, min_buyout)) as avg_price, COUNT(*) as cnt
               FROM price_snapshots
               WHERE item_id = ? AND snapshot_time >= ? AND COALESCE(market_value, min_buyout) IS NOT NULL AND COALESCE(market_value, min_buyout) > 0""",
            (item_id, fourteen_days_ago),
        ).fetchone()

        if not avg_7d_row or not avg_7d_row["avg_price"] or avg_7d_row["cnt"] < 3:
            continue

        avg_7d = avg_7d_row["avg_price"]
        avg_14d = avg_14d_row["avg_price"] if avg_14d_row and avg_14d_row["avg_price"] else avg_7d

        # Day-of-week analysis: raid days vs off days
        # SQLite: strftime('%w', timestamp, 'unixepoch') gives 0=Sunday, 1=Monday, ...
        # We need to convert our RAID_DAYS (0=Monday) to SQLite format (0=Sunday)
        # Monday=0 -> SQLite 1, Tuesday=1 -> 2, Wed=2 -> 3, Thu=3 -> 4, etc.
        sqlite_raid_days = [((d + 1) % 7) for d in RAID_DAYS]
        raid_day_str = ",".join(str(d) for d in sqlite_raid_days)

        raid_avg_row = conn.execute(
            f"""SELECT AVG(COALESCE(market_value, min_buyout)) as avg_price, COUNT(*) as cnt
               FROM price_snapshots
               WHERE item_id = ? AND snapshot_time >= ?
                 AND COALESCE(market_value, min_buyout) IS NOT NULL AND COALESCE(market_value, min_buyout) > 0
                 AND CAST(strftime('%w', snapshot_time, 'unixepoch') AS INTEGER) IN ({raid_day_str})""",
            (item_id, fourteen_days_ago),
        ).fetchone()

        off_avg_row = conn.execute(
            f"""SELECT AVG(COALESCE(market_value, min_buyout)) as avg_price, COUNT(*) as cnt
               FROM price_snapshots
               WHERE item_id = ? AND snapshot_time >= ?
                 AND COALESCE(market_value, min_buyout) IS NOT NULL AND COALESCE(market_value, min_buyout) > 0
                 AND CAST(strftime('%w', snapshot_time, 'unixepoch') AS INTEGER) NOT IN ({raid_day_str})""",
            (item_id, fourteen_days_ago),
        ).fetchone()

        avg_raid_day = raid_avg_row["avg_price"] if raid_avg_row and raid_avg_row["avg_price"] else avg_7d
        avg_off_day = off_avg_row["avg_price"] if off_avg_row and off_avg_row["avg_price"] else avg_7d

        # Calculate discount from 7-day average
        discount_pct = (avg_7d - current_price) / avg_7d if avg_7d > 0 else 0

        # Expected profit if selling at raid day average
        expected_profit_pct = (avg_raid_day - current_price) / current_price if current_price > 0 else 0

        # Confidence: how consistent is the raid-day premium?
        # Higher if raid day average is consistently above off-day average
        # and if we have enough data points
        data_points = (avg_7d_row["cnt"] or 0)
        raid_points = (raid_avg_row["cnt"] or 0) if raid_avg_row else 0
        off_points = (off_avg_row["cnt"] or 0) if off_avg_row else 0

        if avg_off_day > 0 and raid_points >= 2 and off_points >= 2:
            raid_premium = (avg_raid_day - avg_off_day) / avg_off_day
            confidence = min(1.0, max(0.0, raid_premium * 5))  # Scale: 20% premium = 1.0 confidence
            # Adjust for data quantity
            confidence *= min(1.0, data_points / 20)
        else:
            confidence = 0.0

        # Determine signal
        if discount_pct >= BUY_LOW_THRESHOLD and expected_profit_pct >= 0.10 and confidence >= 0.3:
            signal = "strong_buy"
        elif discount_pct >= BUY_LOW_THRESHOLD * 0.6 and expected_profit_pct >= 0.05:
            signal = "buy"
        else:
            signal = "hold"

        recommendations.append({
            "item_id": item_id,
            "name": item["name"],
            "category": item["category"],
            "current_min_buyout": current_price,
            "avg_7d": avg_7d,
            "avg_14d": avg_14d,
            "avg_raid_day_price": avg_raid_day,
            "avg_off_day_price": avg_off_day,
            "discount_pct": discount_pct,
            "expected_profit_pct": expected_profit_pct,
            "confidence": confidence,
            "signal": signal,
            "num_auctions": current_auctions,
        })

    conn.close()

    # Sort: strong_buy first, then buy, then hold; within each group by expected profit
    signal_order = {"strong_buy": 0, "buy": 1, "hold": 2}
    recommendations.sort(key=lambda r: (signal_order.get(r["signal"], 3), -r["expected_profit_pct"]))

    return recommendations


def get_day_of_week_averages(item_id, days=14):
    """Get average prices by day of week for an item.

    Returns: {0: avg_price, 1: avg_price, ...} where 0=Monday, 6=Sunday
    """
    conn = get_db()
    cutoff = int(time.time()) - days * 86400

    rows = conn.execute(
        """SELECT
             CAST(strftime('%w', snapshot_time, 'unixepoch') AS INTEGER) as dow,
             AVG(min_buyout) as avg_price,
             COUNT(*) as cnt
           FROM price_snapshots
           WHERE item_id = ? AND snapshot_time >= ? AND min_buyout IS NOT NULL AND min_buyout > 0
           GROUP BY dow""",
        (item_id, cutoff),
    ).fetchall()
    conn.close()

    # Convert SQLite dow (0=Sun) to our format (0=Mon)
    result = {}
    for row in rows:
        sqlite_dow = row["dow"]  # 0=Sun, 1=Mon, ...
        our_dow = (sqlite_dow - 1) % 7  # 0=Mon, 6=Sun
        result[our_dow] = {"avg_price": row["avg_price"], "count": row["cnt"]}

    return result
