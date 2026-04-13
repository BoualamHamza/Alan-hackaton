# MedBridge — AI Patient Assistant

> Built at the Mistral AI x Alan Hackathon 2026

MedBridge helps patients understand their medical prescriptions and imagery through AI-powered plain-language explanations.

## What it does

| Feature | Description |
|---|---|
| **Prescription analysis** | Upload a prescription photo or PDF → get a clear explanation of each medication |
| **Medical image analysis** | Upload an X-ray, MRI or scan → get a plain-language description |
| **AI chat assistant** | Ask any health question in natural language, at any time |

All medical information is grounded in **MedlinePlus** (U.S. National Library of Medicine).

## Tech stack

- **Backend**: Python + FastAPI
- **Prescription OCR**: Pixtral Large (Mistral)
- **Medical imaging**: MedGemma 4B (Google, HuggingFace) with Pixtral fallback
- **Chat**: Mistral Large + RAG over MedlinePlus
- **Vector DB**: ChromaDB (local)
- **Embeddings**: Mistral Embed

## Quick start

### 1. Clone & install

```bash
git clone <repo-url>
cd MistralxAllan/backend
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your Mistral API key:
# MISTRAL_API_KEY=your_key_here
```

### 3. Build the knowledge base (one-time setup)

```bash
# Download MedlinePlus data
curl -o ../data/medlineplus/mplus_topics.xml \
  https://medlineplus.gov/xml/mplus_topics_2026-04-04.xml

# Parse and index into ChromaDB
python -m backend.apps.assistant.services.medlineplus_parser
python -m backend.apps.assistant.services.vector_store
```

### 4. Start the server

```bash
uvicorn backend.main:app --reload
```

Server runs at `http://localhost:8000`
Interactive API docs at `http://localhost:8000/docs`

## API Endpoints

### Analyze a prescription
```bash
curl -X POST http://localhost:8000/analyze/prescription \
  -F "file=@prescription.jpg"
```

### Analyze a medical image
```bash
curl -X POST http://localhost:8000/analyze/image \
  -F "file=@xray.jpg"
```

### Chat with the assistant
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is paracetamol used for?"}'

# Continue the conversation using the returned session_id
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Can I take it with alcohol?", "session_id": "your-session-id"}'
```

## Demo scenarios

### Scenario 1 — Prescription (common cold)
Upload a prescription containing Paracetamol, Hexaspray, Sterimar.
Expected: clear explanation of each medication, dosage, and instructions in plain language.

### Scenario 2 — Chat assistant
```
Patient: "What is amoxicillin?"
Patient: "How long does it take to work?"
Patient: "What if I miss a dose?"
```
Expected: conversational, accurate, jargon-free answers with MedlinePlus sources.

### Scenario 3 — Medical image (chest X-ray)
Upload a chest X-ray image.
Expected: plain-language description of what is visible, with a reminder to consult the doctor.

## Note on GPU

Medical image analysis uses **MedGemma 4B** when a GPU is available (recommended).
Without GPU, the system automatically falls back to **Pixtral Large**.
