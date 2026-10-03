"""SQLite ledger — the shop's books. No external DB needed."""
import sqlite3
from datetime import date
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sales (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,          -- ISO timestamp
    customer    TEXT NOT NULL,
    item        TEXT NOT NULL,          -- normalized: atta, chini, chawal...
    qty         REAL NOT NULL,
    unit        TEXT NOT NULL,          -- bori | kg | packet ...
    amount_pkr  REAL,                   -- NULL when not spoken
    note        TEXT DEFAULT '',
    source      TEXT DEFAULT 'voice'    -- voice | seed | manual
);
CREATE INDEX IF NOT EXISTS idx_sales_ts ON sales(ts);
"""


def _connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA)


def insert_sale(db_path: str, customer: str, item: str, qty: float, unit: str,
                amount_pkr=None, note: str = "", source: str = "voice") -> int:
    from datetime import datetime
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO sales (ts, customer, item, qty, unit, amount_pkr, note, source)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), customer, item,
             qty, unit, amount_pkr, note, source),
        )
        return cur.lastrowid


def recent_sales(db_path: str, limit: int = 50) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM sales ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def update_last_sale(db_path: str, **fields) -> dict | None:
    """Apply a spoken correction to the most recent entry."""
    allowed = {"customer", "item", "qty", "unit", "amount_pkr", "note"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return None
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 1").fetchone()
        if row is None:
            return None
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(f"UPDATE sales SET {set_clause} WHERE id = ?",
                     (*updates.values(), row["id"]))
        row = conn.execute("SELECT * FROM sales WHERE id = ?", (row["id"],)).fetchone()
    return dict(row)


def daily_summary(db_path: str, day: str | None = None) -> dict:
    day = day or date.today().isoformat()
    with _connect(db_path) as conn:
        agg = conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(amount_pkr), 0) AS total"
            " FROM sales WHERE date(ts) = ?", (day,)
        ).fetchone()
        items = conn.execute(
            "SELECT item, unit, SUM(qty) AS q FROM sales"
            " WHERE date(ts) = ? GROUP BY item, unit ORDER BY q DESC", (day,)
        ).fetchall()
    return {
        "date": day,
        "count": agg["n"],
        "total_amount": agg["total"],
        "by_item": [f"{r['q']:g} {r['unit']} {r['item']}" for r in items],
    }
