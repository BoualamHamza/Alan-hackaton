"""
AgentIA_Article — Main FastAPI app.
Exposes a single endpoint:
  POST /generate/article  →  upload medical report → get HTML article
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import os

from services.report_extractor import extract_report
from services.article_generator import generate_article_content
from services.image_generator import generate_all_images
from services.article_renderer import save_article, render_article

app = FastAPI(
    title="Charly — Article Generator",
    description="Generates a personalized patient health article from a medical report.",
    version="1.0.0",
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "Charly Article Generator"}


@app.post("/generate/article", response_class=HTMLResponse)
async def generate_article(file: UploadFile = File(...)):
    """
    Upload a medical report (JPEG, PNG or PDF).
    Returns a fully rendered HTML article personalized for the patient.

    Pipeline:
      1. Extract medical info from the report (Pixtral / Mistral Large)
      2. Generate article sections via RAG + Mistral Large
      3. Generate medical illustrations via Nano Banana Pro (Gemini)
      4. Render everything as a WHOOP-style HTML article
    """
    # Validate file type
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Accepted: JPEG, PNG, PDF."
        )

    file_bytes = await file.read()

    # Step 2 — Extract medical data from the report
    print(f"\n[1/4] Extracting medical data from '{file.filename}'...")
    medical_data = extract_report(file_bytes, file.filename)
    print(f"      Diagnosis: {medical_data.get('diagnosis')}")

    # Step 3 — Generate article content via RAG + Mistral Large
    print("[2/4] Generating article content...")
    article_content = generate_article_content(medical_data)

    # Step 4 — Generate images via Nano Banana Pro
    print("[3/4] Generating medical illustrations...")
    images = generate_all_images(article_content["image_keywords"])

    # Step 5 — Render HTML article
    print("[4/4] Rendering HTML article...")
    html = render_article(article_content, images)

    # Also save to disk
    safe_name = (medical_data.get("diagnosis") or "article").replace(" ", "_").lower()
    save_article(article_content, images, filename=safe_name)

    print("Done.\n")
    return HTMLResponse(content=html, status_code=200)


@app.post("/generate/article/json")
async def generate_article_json(file: UploadFile = File(...)):
    """
    Same as /generate/article but returns the raw structured content as JSON.
    Useful for debugging or building a custom frontend.
    """
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'.")

    file_bytes = await file.read()

    medical_data = extract_report(file_bytes, file.filename)
    article_content = generate_article_content(medical_data)

    return JSONResponse(content={
        "medical_data": medical_data,
        "article": {
            "title": article_content["title"],
            "intro": article_content["intro"],
            "sections": [
                {"section": s["section"], "content": s["content"]}
                for s in article_content["sections"]
            ],
        },
    })
