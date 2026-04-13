# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

This is a **monorepo** containing the Hippo app (built at the Alan Hackathon):

- `src/` — Next.js 16 frontend (App Router, React 19, Tailwind v4, TypeScript)
- `backend/` — FastAPI backend, a single app that mounts two independent domains:
  - `backend/apps/assistant/` — chat, medical image analysis, article recommendation
  - `backend/apps/medexplain/` — the heavier domain: extracts medical info from documents, reviews it, and synthesizes explainer content (audio, video, diagrams, cards)
- `backend/main.py` — composes both domains into one ASGI app; the entrypoint is `backend.main:app`

Python dependencies are centralized in `backend/requirements.txt`. The per-domain `requirements.txt` files are thin wrappers around the canonical one.

## Common commands

```bash
# Frontend (port 3000)
npm install
npm run dev           # or: npm run dev:web
npm run build
npm run lint          # eslint via eslint-config-next

# Backend (port 8000, docs at /docs)
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
npm run dev:api       # wraps: uvicorn backend.main:app --reload

# Tests (medexplain domain only — pytest with asyncio_mode=auto)
cd backend/apps/medexplain && pytest
cd backend/apps/medexplain && pytest tests/test_extraction.py::test_name   # single test
```

## Architecture notes

### Frontend ↔ Backend contract
- The frontend talks to the backend via `src/lib/api.ts`. Base URL is `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).
- Case creation posts `multipart/form-data` to `POST /cases` — do **not** set `Content-Type` manually; the browser needs to set the multipart boundary.
- `src/lib/mockData.ts` provides fallback/mock cases so the UI works without a running backend. `Navbar` will use a mock case first and only fall through to `getCase()` if no mock exists.

### Backend composition
`backend/main.py` mounts routers from both domains into a single FastAPI app with permissive CORS. When adding a new endpoint, register its router there. The `lifespan` ensures `settings.output_dir` (medexplain outputs) exists on startup.

### MedExplain pipeline
`backend/apps/medexplain/pipeline/` implements the media generation flow (orchestrator → splitter → {audio, avatar, visual, cards, diagrams} → stitcher). Tests in `backend/apps/medexplain/tests/` use `asyncio_mode=auto`, so async test functions don't need an explicit `@pytest.mark.asyncio`.

### Required environment
At minimum:
```
MISTRAL_API_KEY=...
```
Set via a `.env` file. MedExplain has additional settings in `backend/apps/medexplain/config.py`.

## Conventions

- The app is named **Hippo**. The logo lives at `public/logo.jpeg` (copy of the root `logo.jpeg`) and is rendered in `src/components/Navbar.tsx` via `next/image`.
- Frontend uses path alias `@/*` → `src/*` (see `tsconfig.json`).
- Tailwind v4 is wired through `@tailwindcss/postcss`; styling is utility-first, no separate config file.
