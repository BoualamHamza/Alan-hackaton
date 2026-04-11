"""
Handles prescription analysis.
Accepts an image (JPEG/PNG) or PDF file.
- Extracts medication names, dosages and instructions via mistral-small-latest (vision, raw httpx)
- Looks up each medication in the MedlinePlus vector store
- Returns a patient-friendly explanation for each medication
"""

import base64
import io
import json
import time
import os
import httpx
import pdfplumber
from PIL import Image
from mistralai import Mistral

from app.core.config import settings
from app.services.vector_store import retrieve

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
VISION_MODEL = "mistral-small-latest"
MISTRAL_MODEL = "mistral-large-latest"

ENV_PATH = os.path.join(os.path.dirname(__file__), "../../../.env")


def _get_api_key() -> str:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    key = os.environ.get("MISTRAL_API_KEY") or settings.mistral_api_key
    if not key:
        raise ValueError("MISTRAL_API_KEY not set.")
    return key


def _get_client():
    api_key = _get_api_key()
    return Mistral(api_key=api_key)


def call_with_retry(fn, *args, **kwargs):
    """Calls a Mistral API function, retrying with backoff on rate limit."""
    for attempt in range(8):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) or "rate_limited" in str(e):
                wait = 30 * (attempt + 1)
                print(f"Rate limit hit, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Mistral API rate limit — max retries exceeded.")


# ── Helpers ──────────────────────────────────────────────────────────────────

def image_to_base64(image: Image.Image) -> str:
    """Converts a PIL image to a base64-encoded JPEG string."""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def extract_text_from_pdf(file_bytes: bytes) -> str | None:
    """
    Tries to extract text directly from a PDF (works for digital PDFs).
    Returns None if the PDF is image-based (scanned).
    """
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        ).strip()
    return text if len(text) > 50 else None


def pdf_to_images(file_bytes: bytes) -> list[Image.Image]:
    """Converts each page of a scanned PDF into a PIL image."""
    return convert_from_bytes(file_bytes, dpi=200)


# ── Step 1: Extract medication info from file via Pixtral ─────────────────────

def extract_medications_from_image(image: Image.Image) -> list[dict]:
    """
    Sends an image to mistral-small-latest (vision) via raw httpx.
    Returns a list of dicts: [{name, dosage, frequency, duration, instructions}]
    """
    api_key = _get_api_key()
    image_b64 = image_to_base64(image)

    prompt = """You are analyzing a medical prescription image.
Extract all medications listed and return a JSON object with a "medications" array.
For each medication, include:
- "name": the medication name
- "dosage": the dose (e.g. "500mg")
- "frequency": how often to take it (e.g. "twice a day")
- "duration": for how long (e.g. "7 days") or null if not specified
- "instructions": any special instructions (e.g. "take with food") or null

Return ONLY a valid JSON object like: {"medications": [...]}
"""

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"},
                ],
            }
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }

    for attempt in range(10):
        try:
            with httpx.Client(timeout=60.0) as http_client:
                response = http_client.post(
                    MISTRAL_API_URL,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
            if response.status_code == 429:
                wait = min(30 * (2 ** attempt), 300)
                print(f"Rate limit (attempt {attempt+1}/10), waiting {wait}s...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            data = response.json()
            result = json.loads(data["choices"][0]["message"]["content"])
            return result.get("medications", result) if isinstance(result, dict) else result
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            wait = 10 * (attempt + 1)
            print(f"Network error, retrying in {wait}s: {e}")
            time.sleep(wait)

    raise RuntimeError("Mistral vision API — max retries exceeded.")


def extract_medications_from_text(text: str) -> list[dict]:
    """
    Sends prescription text to Mistral Large to extract medication details.
    Used when the PDF has extractable text (no need for vision).
    """
    prompt = f"""You are analyzing a medical prescription text.
Extract all medications listed and return a JSON array.
For each medication, include:
- "name": the medication name
- "dosage": the dose (e.g. "500mg")
- "frequency": how often to take it (e.g. "twice a day")
- "duration": for how long (e.g. "7 days") or null if not specified
- "instructions": any special instructions or null

Return ONLY a valid JSON array, no explanation.

Prescription text:
{text}
"""

    response = call_with_retry(
        _get_client().chat.complete,
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


# ── Step 2: Explain each medication in plain language ─────────────────────────

def explain_medication(medication: dict) -> dict:
    """
    For a single medication dict, retrieves relevant MedlinePlus context
    and generates a patient-friendly explanation using Mistral Large.
    """
    query = f"{medication['name']} {medication.get('dosage', '')} medication"
    context_chunks = retrieve(query, k=4)
    context = "\n\n".join(c["text"] for c in context_chunks)
    sources = list({c["title"] for c in context_chunks})

    prompt = f"""You are a helpful medical assistant explaining a prescription to a patient.
Use simple, clear language. Avoid medical jargon. Be reassuring but honest.

Medication: {medication['name']}
Dosage: {medication.get('dosage', 'not specified')}
Frequency: {medication.get('frequency', 'not specified')}
Duration: {medication.get('duration', 'not specified')}
Special instructions: {medication.get('instructions', 'none')}

Medical reference information:
{context}

Write a short, friendly explanation (3-5 sentences) that answers:
1. What this medication is for
2. How and when to take it
3. Any important warnings or tips

Do not suggest changing the prescribed dose. Always recommend consulting the doctor for questions.
"""

    response = call_with_retry(
        _get_client().chat.complete,
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        **medication,
        "explanation": response.choices[0].message.content.strip(),
        "sources": sources,
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def analyze_prescription(file_bytes: bytes, filename: str) -> dict:
    """
    Main function called by the API endpoint.
    Accepts raw file bytes and the filename.
    Returns structured results with explained medications.
    """
    filename_lower = filename.lower()
    medications = []

    if filename_lower.endswith(".pdf"):
        # Try direct text extraction first
        text = extract_text_from_pdf(file_bytes)
        if text:
            medications = extract_medications_from_text(text)
        else:
            # Scanned PDF: convert first page to image and use Pixtral
            images = pdf_to_images(file_bytes)
            medications = extract_medications_from_image(images[0])
    else:
        # Image file (JPEG, PNG, etc.)
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        medications = extract_medications_from_image(image)

    # Generate a plain-language explanation for each medication
    explained = [explain_medication(med) for med in medications]

    return {
        "medications_found": len(explained),
        "medications": explained,
    }
