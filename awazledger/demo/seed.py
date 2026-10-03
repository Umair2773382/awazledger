"""Seed the ledger with sample entries (for demo rehearsal)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from awaz import db
from awaz.config import settings

SAMPLES = [
    ("Ahmed Khan", "atta", 2, "bori", 6400, "20kg"),
    ("Shah Raziq", "atta", 1, "bori", 3200, "20kg"),
    ("Bilal Ahmed", "chini", 5, "kg", 750, ""),
    ("Gul Rehman", "atta", 3, "bori", 9600, "20kg"),
    ("Ahmed Khan", "ghee", 1, "packet", 2400, "5kg"),
]

if __name__ == "__main__":
    db.init_db(settings.db_path)
    for customer, item, qty, unit, amount, note in SAMPLES:
        db.insert_sale(settings.db_path, customer, item, qty, unit, amount, note, source="seed")
    print(f"Seeded {len(SAMPLES)} entries into {settings.db_path}")
    print(db.daily_summary(settings.db_path))
