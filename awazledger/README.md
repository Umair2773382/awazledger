# 🎙️ AwazLedger — voice-first bookkeeping for shopkeepers

Speak a sale in Urdu → structured ledger entry. Ask *"aaj ka hisab"* → daily summary.
Built for the agentic-AI hackathon: an **agent**, not a chatbot —
transcribe → understand → act on the ledger → report, with multi-turn correction.

## Run locally

```bash
cd awazledger
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-local.txt   # full install incl. offline Whisper
# ...or: pip install -r requirements.txt   # lean install, uses the Groq API
cp .env.example .env
# fill in: LLM key (free: https://aistudio.google.com/apikey)
#          GROQ key (free: https://console.groq.com/keys) — skip if using local Whisper
```

Streamlit UI (same as the hosted demo):

```bash
streamlit run streamlit_app.py   # http://localhost:8501
```

FastAPI + mic page:

```bash
uvicorn web.app:app --reload     # http://localhost:8000
```

Seed demo data: `python demo/seed.py`

`TRANSCRIBE_PROVIDER` in `.env` picks the voice engine:
- `groq` (default) — free Groq API, `whisper-large-v3-turbo`, best quality, needs internet
- `local` — faster-whisper on your machine, fully offline (first run downloads the model)

## How it works

```
mic / voice note (st.audio_input)
      │
      ▼
transcription ──► Groq whisper-large-v3-turbo (free API) or local faster-whisper
      │              "Shah Raziq ko bees kilo atta, ek bori"
      ▼
LLM (strict JSON: intent + fields) ──► record | correct | summary
      │
      ▼
SQLite ledger ◄──► "aaj ka hisab" ──► summary
```

- **Record:** new sale → row in `sales` table.
- **Correct:** *"nahi, do bori thi"* → last entry is fixed, not duplicated.
- **Summary:** *"aaj ka hisab batao"* → count, items, total Rs for the day.

## Deploy — get your public hackathon link (free)

**Streamlit Community Cloud** — free, runs full Python apps, public `*.streamlit.app` URL.
(Hugging Face now charges for all compute Spaces; only Static is free and it can't
run a Python backend — so Streamlit Cloud is the free path.)

1. Free keys: Groq → [console.groq.com/keys](https://console.groq.com/keys),
   Gemini → [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. Create a free [github.com](https://github.com) account → **New repository**
   (public, e.g. `awazledger`) → **uploading an existing file** → drag in all
   project files → Commit.
3. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with GitHub →
   **Create app** → pick your repo, branch `main`, main file `streamlit_app.py`.
4. Before deploying: **Advanced settings → Secrets**, paste (with your real keys):
   ```toml
   LLM_API_KEY = "AIza..."
   LLM_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
   LLM_MODEL = "gemini-2.0-flash"
   GROQ_API_KEY = "gsk_..."
   TRANSCRIBE_PROVIDER = "groq"
   ```
5. **Deploy** (~5 min). Your link looks like
   `https://yourname-awazledger.streamlit.app` — submit that.

**Before judging:** open the link 5 minutes early — free apps sleep when idle
and need a minute to wake up.

## Demo script (3 min)

1. **0:00–0:30** — The pain: small dealers keep books on paper or in memory.
2. **0:30–1:30** — Live: speak 2–3 sales in Urdu, then a correction
   (*"nahi, teen bori thi"*). Ledger updates on screen.
3. **1:30–2:15** — *"Aaj ka hisab batao"* → totals appear.
4. **2:15–3:00** — Close: voice-first ERP for the informal economy. WhatsApp is
   the deployment channel (voice notes people already send).

Rehearsal lines: `demo/sample_phrases.md`. Backup: pre-record clean audio on
your phone in case of hall noise.

## Roadmap (post-hackathon)

- WhatsApp Cloud API as the real input channel (dealers already live there)
- Udhaar (credit) tracking per customer + spoken reminders
- TTS so the agent *speaks* the hisab back
- Pashto + Saraiki coverage as transcription improves
