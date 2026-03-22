"""Flask web application for TSM Price Tracker."""

import os
import time
from flask import Flask, render_template, jsonify, request
from db import init_db, get_db, populate_items, insert_price_snapshots_bulk, insert_trades_bulk
from config import TBC_ITEMS, CATEGORIES, RAID_DAYS, DEPLOYMENT_MODE, PUSH_API_KEY
from tsm_parser import copper_to_gold_float
from analyzer import get_recommendations, get_sell_recommendations, get_day_of_week_averages

# Only import collector in local mode (it needs AppData.lua access)
if DEPLOYMENT_MODE == "local":
    from collector import collect_snapshot

app = Flask(__name__)


def get_icon_url(item_id):
    """Get Wowhead icon CDN URL for an item."""
    item_data = TBC_ITEMS.get(item_id)
    if item_data and len(item_data) > 2:
        return f"https://wow.zamimg.com/images/wow/icons/large/{item_data[2]}.jpg"
    return None


@app.before_request
def ensure_db():
    """Initialize database on first request."""
    if not hasattr(app, "_db_initialized"):
        init_db()
        populate_items(TBC_ITEMS)
        app._db_initialized = True


# --- Pages ---

@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES, raid_days=RAID_DAYS, deployment_mode=DEPLOYMENT_MODE)


# --- API ---

@app.route("/api/items")
def api_items():
    """List all tracked items with categories."""
    conn = get_db()
    items = conn.execute("SELECT item_id, name, category FROM items ORDER BY category, name").fetchall()
    conn.close()
    result = []
    for row in items:
        d = dict(row)
        d["icon_url"] = get_icon_url(d["item_id"])
        result.append(d)
    return jsonify(result)


@app.route("/api/prices/<int:item_id>")
def api_prices(item_id):
    """Get price history for an item. Query params: days (default 30)."""
    days = request.args.get("days", 30, type=int)
    cutoff = int(time.time()) - days * 86400

    conn = get_db()
    rows = conn.execute(
        """SELECT snapshot_time, min_buyout, market_value, market_value_recent, historical, num_auctions
           FROM price_snapshots
           WHERE item_id = ? AND snapshot_time >= ?
           ORDER BY snapshot_time""",
        (item_id, cutoff),
    ).fetchall()

    item = conn.execute("SELECT name, category FROM items WHERE item_id = ?", (item_id,)).fetchone()
    conn.close()

    data = []
    for row in rows:
        data.append({
            "time": row["snapshot_time"],
            "minBuyout": copper_to_gold_float(row["min_buyout"]),
            "marketValue": copper_to_gold_float(row["market_value"]),
            "marketValueRecent": copper_to_gold_float(row["market_value_recent"]),
            "historical": copper_to_gold_float(row["historical"]),
            "numAuctions": row["num_auctions"],
        })

    return jsonify({
        "item_id": item_id,
        "name": item["name"] if item else f"Item {item_id}",
        "category": item["category"] if item else "unknown",
        "data": data,
    })


@app.route("/api/prices/multi")
def api_prices_multi():
    """Get price history for multiple items. Query params: ids (comma-separated), days."""
    ids_str = request.args.get("ids", "")
    days = request.args.get("days", 30, type=int)

    if not ids_str:
        return jsonify({"error": "ids parameter required"}), 400

    item_ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    cutoff = int(time.time()) - days * 86400

    conn = get_db()
    placeholders = ",".join("?" * len(item_ids))

    rows = conn.execute(
        f"""SELECT item_id, snapshot_time, min_buyout, market_value, market_value_recent, num_auctions
           FROM price_snapshots
           WHERE item_id IN ({placeholders}) AND snapshot_time >= ?
           ORDER BY snapshot_time""",
        item_ids + [cutoff],
    ).fetchall()

    items = conn.execute(
        f"SELECT item_id, name, category FROM items WHERE item_id IN ({placeholders})",
        item_ids,
    ).fetchall()
    conn.close()

    items_map = {row["item_id"]: dict(row) for row in items}

    # Group by item
    result = {}
    for row in rows:
        iid = row["item_id"]
        if iid not in result:
            info = items_map.get(iid, {"name": f"Item {iid}", "category": "unknown"})
            result[iid] = {"item_id": iid, "name": info["name"], "category": info["category"], "data": []}
        result[iid]["data"].append({
            "time": row["snapshot_time"],
            "minBuyout": copper_to_gold_float(row["min_buyout"]),
            "marketValue": copper_to_gold_float(row["market_value"]),
            "marketValueRecent": copper_to_gold_float(row["market_value_recent"]),
            "numAuctions": row["num_auctions"],
        })

    return jsonify(list(result.values()))


@app.route("/api/recommendations")
def api_recommendations():
    """Get buy-low recommendations."""
    recs = get_recommendations()
    # Convert copper to gold for display
    for r in recs:
        r["current_min_buyout_gold"] = copper_to_gold_float(r["current_min_buyout"])
        r["avg_7d_gold"] = copper_to_gold_float(r["avg_7d"])
        r["avg_14d_gold"] = copper_to_gold_float(r["avg_14d"])
        r["avg_raid_day_gold"] = copper_to_gold_float(r["avg_raid_day_price"])
        r["avg_off_day_gold"] = copper_to_gold_float(r["avg_off_day_price"])
        r["icon_url"] = get_icon_url(r["item_id"])
    return jsonify(recs)


@app.route("/api/sell-recommendations")
def api_sell_recommendations():
    """Get sell-high recommendations."""
    recs = get_sell_recommendations()
    for r in recs:
        r["current_min_buyout_gold"] = copper_to_gold_float(r["current_min_buyout"])
        r["avg_7d_gold"] = copper_to_gold_float(r["avg_7d"])
        r["avg_raid_day_gold"] = copper_to_gold_float(r["avg_raid_day_price"])
        r["avg_off_day_gold"] = copper_to_gold_float(r["avg_off_day_price"])
        r["icon_url"] = get_icon_url(r["item_id"])
    return jsonify(recs)


@app.route("/api/dow/<int:item_id>")
def api_day_of_week(item_id):
    """Get day-of-week average prices for an item."""
    days = request.args.get("days", 14, type=int)
    dow_data = get_day_of_week_averages(item_id, days)
    # Convert to gold
    result = {}
    for dow, info in dow_data.items():
        result[dow] = {
            "avg_price_gold": copper_to_gold_float(int(info["avg_price"])) if info["avg_price"] else None,
            "count": info["count"],
        }
    return jsonify({"item_id": item_id, "days": days, "day_of_week": result})


@app.route("/api/trades/<int:item_id>")
def api_trades(item_id):
    """Get trade history for an item. Query params: days (default 90), type (buy/sell/all)."""
    days = request.args.get("days", 90, type=int)
    trade_type = request.args.get("type", "all")
    cutoff = int(time.time()) - days * 86400

    conn = get_db()
    if trade_type in ("buy", "sell"):
        rows = conn.execute(
            """SELECT trade_type, quantity, price_per_item, trade_time, player
               FROM trades
               WHERE item_id = ? AND trade_time >= ? AND source = 'Auction' AND trade_type = ?
               ORDER BY trade_time""",
            (item_id, cutoff, trade_type),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT trade_type, quantity, price_per_item, trade_time, player
               FROM trades
               WHERE item_id = ? AND trade_time >= ? AND source = 'Auction'
               ORDER BY trade_time""",
            (item_id, cutoff),
        ).fetchall()

    item = conn.execute("SELECT name FROM items WHERE item_id = ?", (item_id,)).fetchone()
    conn.close()

    data = []
    for row in rows:
        data.append({
            "type": row["trade_type"],
            "quantity": row["quantity"],
            "priceGold": copper_to_gold_float(row["price_per_item"]),
            "time": row["trade_time"],
            "player": row["player"],
        })

    return jsonify({
        "item_id": item_id,
        "name": item["name"] if item else f"Item {item_id}",
        "trades": data,
    })


@app.route("/api/snapshot", methods=["POST"])
def api_snapshot():
    """Trigger a manual data collection from AppData.lua (local mode only)."""
    if DEPLOYMENT_MODE != "local":
        return jsonify({"error": "Snapshot collection not available in cloud mode. Use pusher.py."}), 403
    count = collect_snapshot()
    return jsonify({"status": "ok", "items_collected": count})


@app.route("/api/push", methods=["POST"])
def api_push():
    """Receive price snapshot data pushed from local machine.

    Expected JSON payload:
    {
        "snapshot_time": 1234567890,
        "prices": [
            {"item_id": 21884, "min_buyout": 450000, "market_value": 460000,
             "market_value_recent": 455000, "historical": 448000, "num_auctions": 42},
            ...
        ],
        "trades": [  // optional
            {"item_id": 21884, "trade_type": "buy", "stack_size": 1, "quantity": 5,
             "price_per_item": 450000, "other_player": "", "player": "Mychar",
             "trade_time": 1234567890, "source": "Auction"},
            ...
        ]
    }
    """
    # Validate API key
    auth = request.headers.get("Authorization", "")
    if not PUSH_API_KEY or auth != f"Bearer {PUSH_API_KEY}":
        return jsonify({"error": "Invalid or missing API key"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload"}), 400

    snapshot_time = data.get("snapshot_time")
    prices = data.get("prices", [])
    trades = data.get("trades", [])

    if not snapshot_time or not prices:
        return jsonify({"error": "snapshot_time and prices are required"}), 400

    # Insert price snapshots
    price_rows = []
    for p in prices:
        price_rows.append((
            p["item_id"],
            snapshot_time,
            p.get("min_buyout"),
            p.get("market_value"),
            p.get("market_value_recent"),
            p.get("historical"),
            p.get("num_auctions"),
        ))

    if price_rows:
        insert_price_snapshots_bulk(price_rows)

    # Insert trades if provided
    trade_count = 0
    if trades:
        trade_rows = []
        for t in trades:
            trade_rows.append((
                t["item_id"],
                t["trade_type"],
                t.get("stack_size"),
                t.get("quantity"),
                t.get("price_per_item"),
                t.get("other_player"),
                t.get("player"),
                t["trade_time"],
                t.get("source", "Auction"),
            ))
        insert_trades_bulk(trade_rows)
        trade_count = len(trade_rows)

    return jsonify({
        "status": "ok",
        "prices_received": len(price_rows),
        "trades_received": trade_count,
    })


@app.route("/api/stats")
def api_stats():
    """Get database statistics."""
    conn = get_db()
    total_snapshots = conn.execute("SELECT COUNT(*) as cnt FROM price_snapshots").fetchone()["cnt"]
    total_items = conn.execute("SELECT COUNT(DISTINCT item_id) FROM price_snapshots").fetchone()[0]
    time_range = conn.execute(
        "SELECT MIN(snapshot_time) as earliest, MAX(snapshot_time) as latest FROM price_snapshots"
    ).fetchone()
    total_trades = conn.execute("SELECT COUNT(*) as cnt FROM trades").fetchone()["cnt"]
    trade_range = conn.execute(
        "SELECT MIN(trade_time) as earliest, MAX(trade_time) as latest FROM trades"
    ).fetchone()
    conn.close()

    return jsonify({
        "total_snapshots": total_snapshots,
        "tracked_items": total_items,
        "earliest_snapshot": time_range["earliest"],
        "latest_snapshot": time_range["latest"],
        "total_trades": total_trades,
        "earliest_trade": trade_range["earliest"],
        "latest_trade": trade_range["latest"],
    })


if __name__ == "__main__":
    init_db()
    populate_items(TBC_ITEMS)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=(DEPLOYMENT_MODE == "local"), host="0.0.0.0", port=port)
