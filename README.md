<p align="center">
  <img src="logo.jpeg" alt="Hippo" />
</p>

<h1 align="center">Hippo</h1>

<p align="center">
  <strong>Your AI-powered health companion — turning complex medical journeys into clear, guided paths.</strong>
</p>

<p align="center">
  Built at the <a href="https://alan.com">Alan</a> Hackathon &nbsp;·&nbsp;
  Next.js · FastAPI · Mistral AI
</p>

---

## What is Hippo?

Hippo helps patients navigate their health after a doctor visit. It organises your medical cases, surfaces relevant educational videos and articles, runs interactive health games, and lets you chat with an AI assistant that actually understands your situation.

| Feature | Description |
|---|---|
| Case dashboard | Track all your medical cases in one place |
| AI assistant | Ask questions about your diagnosis, treatments, or medications |
| Educational content | Curated videos & articles matched to your condition |
| Health games | Engaging micro-activities to reinforce health literacy |
| Document vault | Keep prescriptions and reports close at hand |

---

## Quick start

### 1) Frontend

```bash
npm install
npm run dev
# → http://localhost:3000
```

### 2) Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
# → http://localhost:8000  |  docs: /docs
```

### 3) Environment variables

Create a `.env` file and set at minimum:

```bash
MISTRAL_API_KEY=...
```

---

## Tech stack

- **Frontend** — Next.js 14, Tailwind CSS, TypeScript
- **Backend** — FastAPI (Python), multi-domain architecture
- **AI** — Mistral AI for the assistant & medical explainer
- **Data** — MedlinePlus health topics

---

<p align="center">Made with ❤️ and a lot of coffee at the Alan Hackathon</p>
