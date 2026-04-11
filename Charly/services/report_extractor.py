"""
Step 2 — Medical report extraction.
Accepts a JPEG/PNG image or PDF of a medical report.
Uses mistral-small-latest (vision) via raw httpx — approach from colleague's code.
"""

import base64
import io
import json
import time
import os
import httpx
import pdfplumber
from PIL import Image

ENV_PATH = os.path.join(os.path.dirname(__file__), "../../.env")

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
VISION_MODEL = "mistral-small-latest"

EXTRACTION_PROMPT = """You are analyzing a medical document (prescription, report, or letter).
Extract all relevant medical information and return a JSON object with these fields:

- "patient_name": patient's full name if visible, otherwise null
- "date": date of the document if visible, otherwise null
- "diagnosis": the main diagnosis or condition. IMPORTANT: if no diagnosis is explicitly written, INFER it from the medications and context. For example: Doliprane/Paracetamol + Hexaspray (throat) + Sterimar (nasal) → "Nasopharyngitis". Ibuprofen + antibiotic → likely bacterial infection. Always provide a diagnosis, never return null.
- "pathology": the medical pathology or disease category (e.g. "Upper respiratory tract infection", "Metabolic disorder")
- "key_findings": list of key medical findings, symptoms, or relevant patient info (allergies, age, etc.) — list of strings
- "medications": list of medications with dosage and instructions (list of strings)
- "recommendations": doctor's recommendations or instructions (list of strings)
- "lab_results": any lab values mentioned (list of objects with "name" and "value", empty list if none)
- "language": language of the document (e.g. "French", "English")

Return ONLY a valid JSON object, no explanation, no markdown.
"""


def _get_api_key() -> str:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        raise ValueError("MISTRAL_API_KEY not set.")
    return key


def call_mistral_vision(file_bytes: bytes, mime_type: str) -> dict:
    """
    Calls Mistral vision API directly via httpx.
    Supports JPEG, PNG and PDF.
    """
    api_key = _get_api_key()
    b64 = base64.b64encode(file_bytes).decode("utf-8")

    if mime_type == "application/pdf":
        user_content = [
            {"type": "text", "text": EXTRACTION_PROMPT},
            {"type": "document_url", "document_url": f"data:application/pdf;base64,{b64}"},
        ]
    else:
        user_content = [
            {"type": "text", "text": EXTRACTION_PROMPT},
            {"type": "image_url", "image_url": f"data:{mime_type};base64,{b64}"},
        ]

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }

    for attempt in range(10):
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    MISTRAL_API_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

            if response.status_code == 429:
                wait = min(30 * (2 ** attempt), 300)
                print(f"Rate limit (attempt {attempt+1}/10), waiting {wait}s...")
                time.sleep(wait)
                continue

            if response.status_code == 401:
                raise ValueError(f"Unauthorized — check your MISTRAL_API_KEY.")

            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            wait = 10 * (attempt + 1)
            print(f"Network error, retrying in {wait}s: {e}")
            time.sleep(wait)

    raise RuntimeError("Mistral vision API — max retries exceeded.")


def extract_text_from_pdf(file_bytes: bytes) -> str | None:
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
    return text if len(text) > 50 else None


def extract_report(file_bytes: bytes, filename: str) -> dict:
    """
    Main entry point.
    Accepts raw file bytes and filename, returns structured medical data.
    """
    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        # Try text extraction first (faster, no vision needed)
        text = extract_text_from_pdf(file_bytes)
        if text:
            # Send as PDF directly — model handles it
            return call_mistral_vision(file_bytes, "application/pdf")
        else:
            return call_mistral_vision(file_bytes, "application/pdf")
    elif filename_lower.endswith(".png"):
        return call_mistral_vision(file_bytes, "image/png")
    else:
        # JPEG or any other image
        return call_mistral_vision(file_bytes, "image/jpeg")
