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
MISTRAL_MODEL = "mistral-large-latest"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
VISION_MODEL = "mistral-small-latest"

# Global model cache — loaded once, reused across requests
_medgemma_model = None
_medgemma_processor = None


def _get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_medgemma():
    """
    Loads MedGemma model and processor into memory.
    Supports CUDA (NVIDIA), MPS (Apple Silicon), and CPU fallback.
    """
    global _medgemma_model, _medgemma_processor

    if _medgemma_model is not None:
        return  # Already loaded

    device = _get_device()
    print(f"Loading MedGemma 4B on {device}... (first time may take a few minutes)")

    _medgemma_processor = AutoProcessor.from_pretrained(MEDGEMMA_MODEL_ID)
    _medgemma_model = AutoModelForImageTextToText.from_pretrained(
        MEDGEMMA_MODEL_ID,
        torch_dtype=torch.bfloat16 if device in ("cuda", "mps") else torch.float32,
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


# ── Mistral Small fallback (no GPU) ──────────────────────────────────────────

def analyze_with_mistral_vision(image: Image.Image) -> str:
    """
    Fallback: uses mistral-small-latest (vision) via raw httpx when MedGemma unavailable.
    """
    import httpx, time, os
    from dotenv import load_dotenv

    env_path = os.path.join(os.path.dirname(__file__), "../../../.env")
    load_dotenv(dotenv_path=env_path, override=True)
    api_key = os.environ.get("MISTRAL_API_KEY") or settings.mistral_api_key

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    prompt = (
        "You are a medical imaging specialist. "
        "Analyze this medical image and provide a clear, plain-language explanation "
        "suitable for a patient with no medical background. "
        "Describe what you see, what it might indicate, and what the patient should know. "
        "Be accurate, reassuring, and always recommend consulting their doctor for diagnosis."
    )

    payload = {
        "model": VISION_MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"},
        ]}],
        "temperature": 0.2,
    }

    for attempt in range(10):
        try:
            with httpx.Client(timeout=60.0) as http:
                resp = http.post(
                    MISTRAL_API_URL,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
            if resp.status_code == 429:
                wait = min(30 * (2 ** attempt), 300)
                print(f"Rate limit (attempt {attempt+1}/10), waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            time.sleep(10 * (attempt + 1))

    raise RuntimeError("Mistral vision API — max retries exceeded.")


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

    device = _get_device()
    # MedGemma requires the model to be downloaded — use Mistral vision fallback for now
    # At hackathon (H100 with downloaded model), change this back to check device
    use_medgemma = device in ("cuda", "mps") and _medgemma_model is not None
    if use_medgemma:
        print(f"Device {device} — using MedGemma.")
        raw_analysis = analyze_with_medgemma(image)
    else:
        print("Using mistral-small-latest vision (MedGemma not loaded).")
        raw_analysis = analyze_with_mistral_vision(image)

    return enrich_with_context(raw_analysis)
