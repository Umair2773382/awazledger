# AwazLedger on Hugging Face Spaces (Docker)
FROM python:3.11-slim

# ffmpeg decodes the webm/m4a voice notes browsers send
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Whisper model at build time so the first
# transcription is instant (no waiting when judges open the link)
ARG WHISPER_MODEL=small
ENV WHISPER_MODEL=${WHISPER_MODEL}
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('${WHISPER_MODEL}', compute_type='int8')"

COPY . .

ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "uvicorn web.app:app --host 0.0.0.0 --port ${PORT}"]
