# Pediatric Handoff PHI Remover

HIPAA-compliant web application that transcribes pediatric patient handoff recordings and removes all Protected Health Information (PHI) before displaying the transcript.

**All processing happens locally—no patient data ever leaves your machine.**

## Features

- Browser-based audio recording
- Local speech-to-text with Whisper
- Automatic PHI de-identification with Microsoft Presidio
- Custom recognizers for pediatric context (guardian names, MRN, room numbers)
- Copy/download de-identified transcripts

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Frontend)                        │
│  - Record audio via MediaRecorder API                           │
│  - Upload audio files (.webm, .wav, .mp3, .m4a)                 │
│  - Display de-identified transcript with PHI statistics          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (Python/FastAPI)                     │
│                                                                  │
│  POST /api/process receives audio file                          │
│              │                                                   │
│              ▼                                                   │
│  Step 1: Transcribe with faster-whisper (LOCAL)                 │
│              │                                                   │
│              ▼                                                   │
│  Step 2: De-identify with Presidio + custom recognizers         │
│              │                                                   │
│              ▼                                                   │
│  Return: clean_transcript + phi_statistics                      │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Joshausha/pediatric-handoff-phi-remover.git
cd pediatric-handoff-phi-remover

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_lg

# Start the server
uvicorn app.main:app --reload
```

Open http://localhost:8000 in your browser.

## Configuration

Copy `.env.example` to `.env` and adjust settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `WHISPER_MODEL` | `medium.en` | Whisper model size |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `PHI_SCORE_THRESHOLD` | `0.35` | Lower = more aggressive PHI detection |

## Privacy Guarantee

- Audio transcription uses local Whisper (never cloud APIs)
- PHI removal uses Microsoft Presidio running locally
- No external API calls with patient data
- Audio files are processed in memory, not stored

## Testing

```bash
pytest tests/ -v
```

## License

MIT
