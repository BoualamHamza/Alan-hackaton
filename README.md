# Alan Hackathon App

Unified repository for:
- **Frontend**: Next.js app (patient-facing UI)
- **Backend**: FastAPI app that serves both Assistant + MedExplain domains

## Quick start (single source of truth)

### 1) Frontend setup

```bash
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`.

### 2) Backend setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Backend runs on `http://localhost:8000` and docs are available at `http://localhost:8000/docs`.

### 3) Environment variables

Create a `.env` file where needed and configure at least:

```bash
MISTRAL_API_KEY=...
```

## Notes

- Python dependencies are centralized in `backend/requirements.txt`.
- Domain-level requirements files are thin wrappers around that canonical file.
