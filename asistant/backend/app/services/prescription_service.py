"""
Handles prescription analysis.
Accepts an image (JPEG/PNG) or PDF file.
- Extracts medication names, dosages and instructions via Pixtral
- Looks up each medication in the MedlinePlus vector store
- Returns a patient-friendly explanation for each medication
"""

import base64
import io
import json
import time
import pdfplumber
from pdf2image import convert_from_bytes
from PIL import Image
from mistralai import Mistral

from app.core.config import settings
from app.services.vector_store import retrieve

client = Mistral(api_key=settings.mistral_api_key)


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

PIXTRAL_MODEL = "pixtral-large-latest"
MISTRAL_MODEL = "mistral-large-latest"


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
    Sends an image to Pixtral and asks it to extract medication details.
    Returns a list of dicts: [{name, dosage, frequency, duration, instructions}]
    """
    image_b64 = image_to_base64(image)

    prompt = """You are analyzing a medical prescription image.
Extract all medications listed and return a JSON array.
For each medication, include:
- "name": the medication name
- "dosage": the dose (e.g. "500mg")
- "frequency": how often to take it (e.g. "twice a day")
- "duration": for how long (e.g. "7 days") or null if not specified
- "instructions": any special instructions (e.g. "take with food") or null

Return ONLY a valid JSON array, no explanation. Example:
[{"name": "Amoxicillin", "dosage": "500mg", "frequency": "3 times a day", "duration": "7 days", "instructions": "take with food"}]
"""

    response = call_with_retry(
        client.chat.complete,
        model=PIXTRAL_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    raw = response.choices[0].message.content.strip()

    # Clean up potential markdown code blocks
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


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
        client.chat.complete,
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
        client.chat.complete,
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
