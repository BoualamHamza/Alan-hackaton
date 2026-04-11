"""
Handles medical image analysis (X-rays, MRI, CT scans, etc.)
Uses MedGemma 4B (Google, open-source via HuggingFace) for specialized medical vision.
Falls back to Pixtral if MedGemma is not available.

MedGemma runs locally — requires GPU for reasonable speed.
At the hackathon, run on Nebius H100.
"""

import io
import base64
import torch
import pdfplumber
from pdf2image import convert_from_bytes
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText
from mistralai import Mistral

from app.core.config import settings
from app.services.vector_store import retrieve
from app.services.prescription_service import call_with_retry

MEDGEMMA_MODEL_ID = "google/medgemma-4b-it"
PIXTRAL_MODEL = "pixtral-large-latest"
MISTRAL_MODEL = "mistral-large-latest"

# Global model cache — loaded once, reused across requests
_medgemma_model = None
_medgemma_processor = None


def load_medgemma():
    """
    Loads MedGemma model and processor into memory.
    Called once at startup. Requires ~8GB VRAM (GPU) or RAM (CPU, slow).
    """
    global _medgemma_model, _medgemma_processor

    if _medgemma_model is not None:
        return  # Already loaded

    print("Loading MedGemma 4B... (first time may take a few minutes)")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    _medgemma_processor = AutoProcessor.from_pretrained(MEDGEMMA_MODEL_ID)
    _medgemma_model = AutoModelForImageTextToText.from_pretrained(
        MEDGEMMA_MODEL_ID,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
    ).to(device)

    print(f"MedGemma loaded on {device}.")


# ── Image loading ─────────────────────────────────────────────────────────────

def load_image_from_bytes(file_bytes: bytes, filename: str) -> Image.Image:
    """
    Loads the first usable image from the uploaded file.
    Handles JPEG/PNG directly, and both text and scanned PDFs.
    """
    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        # Try to extract embedded images from PDF pages
        images = convert_from_bytes(file_bytes, dpi=200)
        if not images:
            raise ValueError("Could not extract any image from the PDF.")
        return images[0].convert("RGB")
    else:
        return Image.open(io.BytesIO(file_bytes)).convert("RGB")


# ── MedGemma analysis ─────────────────────────────────────────────────────────

def analyze_with_medgemma(image: Image.Image) -> str:
    """
    Sends a medical image to MedGemma and returns its interpretation.
    """
    load_medgemma()
    device = next(_medgemma_model.parameters()).device

    prompt = (
        "You are a medical imaging specialist. "
        "Analyze this medical image and provide a clear, plain-language explanation "
        "suitable for a patient with no medical background. "
        "Describe what you see, what it might indicate, and what the patient should know. "
        "Be accurate, reassuring, and always recommend consulting their doctor for diagnosis."
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    inputs = _medgemma_processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to(device)

    input_len = inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        outputs = _medgemma_model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
        )

    decoded = _medgemma_processor.decode(
        outputs[0][input_len:], skip_special_tokens=True
    )
    return decoded.strip()


# ── Pixtral fallback ──────────────────────────────────────────────────────────

def analyze_with_pixtral(image: Image.Image) -> str:
    """
    Fallback: uses Pixtral if MedGemma is unavailable (no GPU).
    """
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    client = Mistral(api_key=settings.mistral_api_key)

    prompt = (
        "You are a medical imaging specialist. "
        "Analyze this medical image and provide a clear, plain-language explanation "
        "suitable for a patient with no medical background. "
        "Describe what you see, what it might indicate, and what the patient should know. "
        "Be accurate, reassuring, and always recommend consulting their doctor for diagnosis."
    )

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
    return response.choices[0].message.content.strip()


# ── Enrich with MedlinePlus context ──────────────────────────────────────────

def enrich_with_context(raw_analysis: str) -> dict:
    """
    Takes the raw MedGemma/Pixtral output, queries MedlinePlus for related info,
    and uses Mistral Large to produce a final clean patient-friendly explanation.
    """
    context_chunks = retrieve(raw_analysis[:300], k=4)
    context = "\n\n".join(c["text"] for c in context_chunks)
    sources = list({c["title"] for c in context_chunks})

    client = Mistral(api_key=settings.mistral_api_key)

    prompt = f"""You are a compassionate medical assistant helping a patient understand their medical image result.

Initial image analysis:
{raw_analysis}

Additional medical reference:
{context}

Write a final patient-friendly explanation (4-6 sentences) that:
1. Describes what was seen in the image in simple terms
2. Explains what this generally means for health
3. Lists any important things to watch for
4. Reminds the patient to discuss results with their doctor

Use simple language. Be reassuring but honest. Never make a diagnosis.
"""

    response = call_with_retry(
        client.chat.complete,
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "raw_analysis": raw_analysis,
        "patient_explanation": response.choices[0].message.content.strip(),
        "sources": sources,
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def analyze_medical_image(file_bytes: bytes, filename: str) -> dict:
    """
    Main function called by the API endpoint.
    Returns a structured result with the patient-friendly explanation.
    """
    image = load_image_from_bytes(file_bytes, filename)

    # Use MedGemma if GPU available, otherwise fall back to Pixtral
    if torch.cuda.is_available():
        print("GPU detected — using MedGemma.")
        raw_analysis = analyze_with_medgemma(image)
    else:
        print("No GPU — falling back to Pixtral.")
        raw_analysis = analyze_with_pixtral(image)

    return enrich_with_context(raw_analysis)
