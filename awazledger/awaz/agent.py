"""The agent loop: voice note -> transcript -> action -> ledger -> reply.

Keeps the pipeline swappable for tests: pass stub transcribe/parse functions.
"""
from . import db
from .config import settings


def render_summary(s: dict) -> str:
    lines = [f"Aaj ka hisab ({s['date']}): {s['count']} sales"]
    lines.extend(f"- {line}" for line in s["by_item"])
    if s["total_amount"]:
        lines.append(f"Total: Rs {s['total_amount']:,.0f}")
    else:
        lines.append("Total amount: not recorded for these entries")
    return "\n".join(lines)


def _fmt_entry(row: dict) -> str:
    base = f"{row['customer']}: {row['qty']:g} {row['unit']} {row['item']}"
    if row.get("amount_pkr"):
        base += f" — Rs {row['amount_pkr']:,.0f}"
    return base


def handle_voice_note(audio_path: str, transcribe_fn=None, parse_fn=None) -> dict:
    """Full pipeline for one voice note. Returns a JSON-serializable result."""
    from . import transcribe as transcribe_mod
    from . import extract as extract_mod

    transcribe_fn = transcribe_fn or transcribe_mod.transcribe
    parse_fn = parse_fn or extract_mod.parse_note
    db_path = settings.db_path
    db.init_db(db_path)

    t = transcribe_fn(audio_path)
    text = (t.get("text") or "").strip()
    if not text:
        return {"ok": False, "transcript": "", "message": "Kuch sunai nahi diya — dobara bolein."}

    parsed = parse_fn(text)
    intent = parsed.get("intent", "record")

    if intent == "record":
        row_id = db.insert_sale(
            db_path,
            customer=parsed.get("customer") or "Unknown",
            item=parsed.get("item") or "item",
            qty=float(parsed.get("quantity") or 0),
            unit=parsed.get("unit") or "unit",
            amount_pkr=parsed.get("amount_pkr"),
            note=parsed.get("note") or "",
        )
        row = [r for r in db.recent_sales(db_path, 1)][0]
        return {
            "ok": True, "transcript": text, "intent": intent, "entry_id": row_id,
            "message": f"✔ Entry ho gai: {_fmt_entry(row)}",
        }

    if intent == "correct":
        updated = db.update_last_sale(
            db_path,
            customer=parsed.get("customer"),
            item=parsed.get("item"),
            qty=float(parsed["quantity"]) if parsed.get("quantity") else None,
            unit=parsed.get("unit"),
            amount_pkr=parsed.get("amount_pkr"),
            note=parsed.get("note") or None,
        )
        if updated is None:
            return {"ok": False, "transcript": text, "intent": intent,
                    "message": "Theek karne ke liye koi entry nahi mili."}
        return {"ok": True, "transcript": text, "intent": intent,
                "message": f"✔ Theek ho gaya: {_fmt_entry(updated)}"}

    if intent == "summary":
        s = db.daily_summary(db_path)
        return {"ok": True, "transcript": text, "intent": intent,
                "message": render_summary(s), "summary": s}

    return {"ok": False, "transcript": text,
            "message": f"Samajh nahi aaya (intent: {intent}). Dobara bolein."}
