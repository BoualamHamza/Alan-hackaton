# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**MedExplain** — a Python/FastAPI engine that transforms a French medical report (*compte rendu médical*) into two short patient explanation videos (~90s each).

All product requirements and design decisions are in `docs/`. Read those files before making architectural changes.

## Commands

```bash
cd medexplain

# Create and activate virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in API keys
cp .env.example .env

# Run the API
uvicorn main:app --reload

# Run all tests
pytest

# Run a single test file
pytest tests/test_extraction.py -v

# Run a single test
pytest tests/test_models.py::test_validate_total_duration_exceeded -v
```

## Architecture

The engine is a 4-layer sequential pipeline exposed via FastAPI:

```
POST /extract        → Layer 1: Mistral reads the report → PatientDataObject (JSON)
POST /review/approve → Layer 2: Doctor confirms extracted data
POST /review/correct → Layer 2: Doctor applies corrections + confirms
POST /generate       → Layer 3+4: Scripts + video production → two .mp4 files
```

`/generate` requires `doctor_approved: true` on the PDO — it returns 422 otherwise.

### The Patient Data Object (PDO)

The PDO (`models/patient_data.py`) is the central data structure flowing through every layer. It contains clinical facts, plain-language versions, a **scene plan for both videos** (defined at extraction time), and safety flags.

`validate_pdo()` enforces 6 hard rules before the pipeline runs:
1. Required fields non-null
2. Total scene duration ≤ 110s per video
3. Each video starts and ends with an avatar scene
4. No more than 2 consecutive same-type scenes
5. Every visual scene has a `visual_cue`
6. `requires_doctor_review` resolved by doctor approval

### Layer 1 — Extraction (`extraction/`)

`extractor.py` calls `mistral-large-latest` with `timeout_ms=120_000` set at **client init** (not per-call — the SDK ignores per-call timeout). Uses `ResponseFormat(type="json_object")` from `mistralai.client.models`.

Post-processing in `extractor.py`:
- `_normalise_scene_plan()` scales scene durations down if total exceeds 110s (Mistral often returns over-long plans)
- Safety flags cascade into `requires_doctor_review`
- `FollowUp.additional_referrals` has a validator that coerces dicts to strings (Mistral sometimes returns objects instead of plain strings)

### Layer 2 — Review (`review/reviewer.py`)

`approve()` accepts optional dot-notation corrections e.g. `{"video_1_disease.severity.level": "mild"}`, applies them via `apply_corrections()`, stamps `doctor_approved=True`, and calls `validate_pdo()`.

### Layer 3 — Script Generation (`script/generator.py`)

Called once per video. Mistral writes narration text for each scene (~130 words/minute). The response may be `{"scenes": [...]}` or a bare list — both are handled. Returns `(scene_narrations, full_script)`.

### Layer 4 — Video Production (`pipeline/`)

The orchestrator (`orchestrator.py`) runs both videos concurrently via `asyncio.gather`. All blocking calls (ElevenLabs, D-ID, FFmpeg) run in `loop.run_in_executor`. For each video:

1. **`audio.py`** — ElevenLabs official SDK (`elevenlabs` package), `convert_with_timestamps()`. Response attribute is `audio_base_64` (note underscore before 64) and `alignment` (SDK object, not dict). Alignment is character-level; `_build_word_alignment()` rebuilds word-level boundaries.
2. **`splitter.py`** — Snaps cuts to nearest word boundary, cuts per-scene `.mp3` clips via `subprocess` FFmpeg (stream copy, no re-encode).
3. Scene renderers run **in parallel**:
   - **`avatar.py`** — Uses D-ID **Clips API** (`POST /clips`, `GET /clips/{id}`), not the Talks API. Presenter ID is hardcoded: `v2_public_Amber_BlackJacket_HomeOffice@9WuHtiUDnL`. Audio is uploaded to `POST /audios` first; the returned S3 URL is passed directly as `audio_url`. Script type must be `"audio"`.
   - **`visual.py`** — Fetches image via Unsplash or generates a placeholder via FFmpeg, then combines with audio using FFmpeg (`-loop 1 -shortest`).
4. **`stitcher.py`** — FFmpeg concat demuxer joins all scene clips in order → `video_N.mp4`.

**Critical:** audio is generated as one continuous ElevenLabs track then cut per scene — never re-generated per scene. This keeps the voice seamless across transitions.

### External services

| Service | Module | Key detail |
|---------|--------|------------|
| Mistral | `extraction/extractor.py`, `script/generator.py` | `mistral-large-latest`; timeout set at client init: `Mistral(api_key=..., timeout_ms=120_000)` |
| ElevenLabs | `pipeline/audio.py` | Official `elevenlabs` SDK; response fields: `audio_base_64`, `alignment.characters`, `alignment.character_start_times_seconds` |
| D-ID | `pipeline/avatar.py` | **Clips API** (`/clips`), not Talks API; presenter `v2_public_Amber_BlackJacket_HomeOffice@9WuHtiUDnL`; auth: `Basic {did_api_key}` |
| FFmpeg | `pipeline/splitter.py`, `visual.py`, `stitcher.py` | Called via `subprocess.run`; must be installed on the system |

### Known Mistral behaviour to handle

- `additional_referrals` sometimes returned as list of dicts → coerced in `FollowUp` validator
- Scene plan durations often exceed 110s → normalised in `_normalise_scene_plan()`
- Script response wrapped in `{"scenes": [...]}` or bare list → both handled in `generator.py`

## Tests

All external services are mocked. The `sample_pdo` fixture in `tests/conftest.py` provides a valid approved PDO (Alzheimer's report scenario). Video 2 scene plan totals 106s (7 scenes at 14–16s each) — keep it under 110s if modifying the fixture.

Run the full suite before pushing: `pytest` from `medexplain/`.
