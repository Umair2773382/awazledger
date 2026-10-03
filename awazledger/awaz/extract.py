"""Transcript -> structured bookkeeping action via an LLM.

One call does intent classification + field extraction and returns strict JSON.
Works with any OpenAI-compatible API (OpenAI, Gemini via its OpenAI endpoint, ...).
"""
import json
import os

from .config import settings

SYSTEM = """You are AwazLedger's bookkeeping parser for Pakistani shopkeepers.
Input is a transcribed voice note: Urdu (Arabic or Roman script) mixed with English.
Output STRICT JSON only — no markdown, no explanation.

Schema:
{
  "intent": "record" | "correct" | "summary",
  "customer": string | null,
  "item": string | null,
  "quantity": number | null,
  "unit": string | null,
  "amount_pkr": number | null,
  "note": string
}

Rules:
- intent "record": a new sale entry.
- intent "correct": the speaker is fixing the previous entry
  (e.g. "nahi, do bori thi", "rate theek karo, 3200 tha"). Fill ONLY the fields
  being corrected; leave the rest null.
- intent "summary": the speaker asks for the accounts
  (e.g. "aaj ka hisab", "aaj kitni sale hui", "hisab batao").
- Normalize units: bori/bora/bag -> "bori"; kilo/kiloo -> "kg"; packet -> "packet".
- Normalize items to simple lowercase: atta, chini, chawal, ghee, oil, dal, namak...
- quantity = how many units were sold (e.g. 2 bori -> quantity 2, unit "bori").
  Put weight/size detail ("20kg wali") in "note".
- amount_pkr: number only, null when not mentioned. Convert spoken numbers
  ("teen hazaar do sau" -> 3200).
- customer: person's name as spoken; null if not mentioned.

Examples:
IN: "Shah Raziq ko bees kilo atta, ek bori"
OUT: {"intent":"record","customer":"Shah Raziq","item":"atta","quantity":1,"unit":"bori","amount_pkr":null,"note":"20kg"}
IN: "Nahi, do bori thi, ek nahi"
OUT: {"intent":"correct","customer":null,"item":null,"quantity":2,"unit":"bori","amount_pkr":null,"note":""}
IN: "Aaj ka hisab batao"
OUT: {"intent":"summary","customer":null,"item":null,"quantity":null,"unit":null,"amount_pkr":null,"note":""}
"""


def get_client():
    from openai import OpenAI

    # One Groq key can power both transcription and understanding.
    api_key = settings.llm_api_key or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("LLM_API_KEY (or GROQ_API_KEY) is not set — see .env.example")
    return OpenAI(api_key=api_key, base_url=settings.llm_base_url)


def _parse_json(text: str) -> dict:
    """Parse JSON even if the model wrapped it in markdown fences."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        t = t.rsplit("```", 1)[0]
    return json.loads(t.strip())


def parse_note(text: str) -> dict:
    """Classify intent + extract fields from a transcript. Returns the JSON dict."""
    client = get_client()
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": text},
    ]
    try:
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
    except Exception:
        # Some providers/models don't support JSON mode — retry plain and
        # strip any fences from the reply instead.
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0,
        )
    return _parse_json(resp.choices[0].message.content)
