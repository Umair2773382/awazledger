"""FastAPI server — serves the UI and the voice API."""
import shutil
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()  # must run before awaz.config is imported

from awaz import agent, db
from awaz.config import settings

app = FastAPI(title="AwazLedger")

HERE = Path(__file__).parent
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(HERE / "static" / "index.html")


@app.post("/api/voice")
async def voice_note(audio: UploadFile = File(...)):
    suffix = Path(audio.filename or "note.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(audio.file, tmp)
        tmp_path = tmp.name
    try:
        return agent.handle_voice_note(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@app.get("/api/ledger")
def ledger(limit: int = 50):
    db.init_db(settings.db_path)
    return db.recent_sales(settings.db_path, limit)


@app.get("/api/summary")
def summary():
    db.init_db(settings.db_path)
    s = db.daily_summary(settings.db_path)
    return {"message": agent.render_summary(s), **s}
