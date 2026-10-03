"""AwazLedger — Streamlit UI.

This is also the entry point for Streamlit Community Cloud (free hosting):
deploy this repo, set Main file path to `streamlit_app.py`, and you get a
public *.streamlit.app link.

The agent pipeline (transcribe -> parse -> ledger -> summary) lives in awaz/
and is shared with the FastAPI version in web/app.py.
"""
import os
import tempfile
from pathlib import Path

import streamlit as st

# Bridge Streamlit Cloud secrets -> env vars (harmless locally).
try:
    for _k in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL",
               "GROQ_API_KEY", "TRANSCRIBE_PROVIDER", "DB_PATH"):
        if _k in st.secrets:
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass
os.environ.setdefault("TRANSCRIBE_PROVIDER", "groq")

from dotenv import load_dotenv

load_dotenv()

from awaz import agent, db
from awaz.config import settings

st.set_page_config(page_title="AwazLedger — آواز لیجر", page_icon="🎙️")
db.init_db(settings.db_path)

st.title("🎙️ AwazLedger — آواز لیجر")
st.caption(
    "Speak a sale in Urdu → structured ledger entry. "
    "Try: “Shah Raziq ko bees kilo atta, ek bori” — "
    "fix it with “nahi, do bori thi” — or ask “aaj ka hisab batao”."
)

audio = st.audio_input("Voice note — tap the mic to record")

if st.button("Submit entry", type="primary", disabled=audio is None):
    with st.spinner("Sun rahe hain…"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(audio.getvalue())
            tmp_path = tmp.name
        try:
            result = agent.handle_voice_note(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    if result.get("transcript"):
        st.caption(f"“{result['transcript']}”")
    if result.get("ok"):
        st.success(result["message"])
    else:
        st.error(result["message"])

st.divider()

if st.button("Aaj ka hisab"):
    s = db.daily_summary(settings.db_path)
    st.text(agent.render_summary(s))

rows = db.recent_sales(settings.db_path, 20)
if rows:
    st.dataframe(
        [
            {
                "Customer": r["customer"],
                "Item": r["item"],
                "Qty": f"{r['qty']:g} {r['unit']}",
                "Amount": f"Rs {r['amount_pkr']:,.0f}" if r["amount_pkr"] else "—",
            }
            for r in rows
        ],
        use_container_width=True,
    )
else:
    st.info("No entries yet — record your first sale above.")
