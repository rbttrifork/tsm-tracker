"""Database initialization and helpers for TSM Price Tracker."""

import sqlite3
from config import DB_PATH


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT
        );

        CREATE TABLE IF NOT EXISTS price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            snapshot_time INTEGER NOT NULL,
            min_buyout INTEGER,
            market_value INTEGER,           -- dbmarket
            market_value_recent INTEGER,
            historical INTEGER,
            num_auctions INTEGER,
            UNIQUE(item_id, snapshot_time)
        );

        CREATE INDEX IF NOT EXISTS idx_snapshots_item_time
            ON price_snapshots(item_id, snapshot_time);

        CREATE INDEX IF NOT EXISTS idx_snapshots_time
            ON price_snapshots(snapshot_time);

        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            trade_type TEXT NOT NULL,  -- 'buy' or 'sell'
            stack_size INTEGER,
            quantity INTEGER,
            price_per_item INTEGER,    -- copper
            other_player TEXT,
            player TEXT,
            trade_time INTEGER NOT NULL,
            source TEXT,               -- 'Auction', 'Vendor', etc.
            UNIQUE(item_id, trade_type, price_per_item, trade_time, player)
        );

        CREATE INDEX IF NOT EXISTS idx_trades_item_time
            ON trades(item_id, trade_time);

        CREATE INDEX IF NOT EXISTS idx_trades_time
            ON trades(trade_time);
    """)
    conn.commit()
    conn.close()


def populate_items(tbc_items):
    """Insert/update the items table from the TBC_ITEMS config dict."""
    conn = get_db()
    for item_id, item_data in tbc_items.items():
        name, category = item_data[0], item_data[1]
        conn.execute(
            "INSERT OR REPLACE INTO items (item_id, name, category) VALUES (?, ?, ?)",
            (item_id, name, category),
        )
    conn.commit()
    conn.close()


def insert_price_snapshot(item_id, snapshot_time, min_buyout, market_value_recent, historical, num_auctions):
    """Insert a single price snapshot, ignoring duplicates."""
    conn = get_db()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO price_snapshots
               (item_id, snapshot_time, min_buyout, market_value_recent, historical, num_auctions)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (item_id, snapshot_time, min_buyout, market_value_recent, historical, num_auctions),
        )
        conn.commit()
    finally:
        conn.close()


def insert_price_snapshots_bulk(rows):
    """Insert many price snapshots at once. rows: list of (item_id, snapshot_time, min_buyout, market_value, market_value_recent, historical, num_auctions)."""
    conn = get_db()
    try:
        conn.executemany(
            """INSERT OR IGNORE INTO price_snapshots
               (item_id, snapshot_time, min_buyout, market_value, market_value_recent, historical, num_auctions)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def insert_trades_bulk(rows):
    """Insert trade records. rows: list of (item_id, trade_type, stack_size, quantity, price_per_item, other_player, player, trade_time, source)."""
    conn = get_db()
    try:
        conn.executemany(
            """INSERT OR IGNORE INTO trades
               (item_id, trade_type, stack_size, quantity, price_per_item, other_player, player, trade_time, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        conn.commit()
    finally:
        conn.close()
