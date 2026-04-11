"""
Step 3 — Article content generation.
Retrieves MedlinePlus context via RAG (ChromaDB) and generates each article
section using Mistral Large. All content in English, addressed directly to the patient.
"""

import os
import json
import time
import chromadb
from mistralai import Mistral

ENV_PATH = os.path.join(os.path.dirname(__file__), "../../.env")

MISTRAL_MODEL = "mistral-large-latest"
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../../data/chroma")
COLLECTION_NAME = "medlineplus"

RULES = """
STRICT RULES — follow all of them:
- Write ONLY in English.
- Address the patient directly using "you" and "your" (never "the patient").
- Do NOT start with meta-phrases like "Here is...", "This section covers...", "Sure!", "Certainly!", "Here's a simple explanation:", "Of course!" or any similar opener. Jump straight into the content.
- Do NOT include section titles or headings — just the content.
- Do NOT use French words or phrases.
- Do NOT use emojis.
- Write in a warm, clear, reassuring tone — like a trusted doctor explaining something important in plain language.
- Use **bold** (markdown) strategically to highlight the most important words or phrases — key terms, critical numbers, important actions. Not more than 2-3 per paragraph.
- Start each section with a short, engaging opening sentence that draws the reader in — a surprising fact, a relatable situation, or a direct statement that makes them want to keep reading. Keep it professional, never sensationalist.
- Keep paragraphs short (3-5 sentences max) so the article feels easy to read.
- Return only the text content, nothing else.
"""


def _get_client():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        raise ValueError("MISTRAL_API_KEY not set.")
    return Mistral(api_key=key)


def call_with_retry(fn, *args, **kwargs):
    for attempt in range(15):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) or "rate_limited" in str(e) or "503" in str(e):
                wait = min(60 * (2 ** attempt), 600)
                print(f"Rate limit (attempt {attempt+1}/15), waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Mistral API — max retries exceeded.")


def retrieve(query: str, k: int = 5) -> list[dict]:
    client = _get_client()
    response = call_with_retry(
        client.embeddings.create,
        model="mistral-embed",
        inputs=[query],
    )
    query_embedding = response.data[0].embedding

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_collection(COLLECTION_NAME)
    results = collection.query(query_embeddings=[query_embedding], n_results=k)

    return [
        {
            "text": results["documents"][0][i],
            "title": results["metadatas"][0][i]["title"],
            "url": results["metadatas"][0][i]["url"],
        }
        for i in range(len(results["documents"][0]))
    ]


def generate_section(prompt: str) -> str:
    client = _get_client()
    response = call_with_retry(
        client.chat.complete,
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


# ── Section generators ─────────────────────────────────────────────────────────

def gen_intro(medical_data: dict) -> dict:
    diagnosis = medical_data.get("diagnosis") or "your condition"
    findings = medical_data.get("key_findings", [])

    chunks = retrieve(f"{diagnosis} overview patient education", k=3)
    context = "\n\n".join(c["text"] for c in chunks)

    prompt = f"""Write the opening of a personalized patient health article about: {diagnosis}

Patient's key findings: {', '.join(findings) if findings else 'none'}

Medical reference:
{context}

Write:
1. A compelling, patient-friendly article title (not clinical — make it feel personal and empowering)
2. A short introduction (3-4 sentences) addressed directly to the patient using "you":
   - Acknowledge what they are dealing with
   - Reassure them that this article will help them understand
   - Set a warm, clear, educational tone

{RULES}
Return JSON with keys "title" and "intro" only. No markdown, no extra fields.
"""
    raw = generate_section(prompt)
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw.strip())
    return {
        "title": result.get("title", diagnosis),
        "intro": result.get("intro", ""),
        "image_keyword": f"{diagnosis} medical",
        "sources": [c["url"] for c in chunks if c["url"]],
    }


def gen_what_you_have(medical_data: dict) -> dict:
    diagnosis = medical_data.get("diagnosis") or "your condition"
    pathology = medical_data.get("pathology", "")
    lab_results = medical_data.get("lab_results", [])

    chunks = retrieve(f"{diagnosis} {pathology} definition symptoms causes", k=5)
    context = "\n\n".join(c["text"] for c in chunks)

    lab_text = ""
    if lab_results:
        lab_text = "Lab results to explain: " + ", ".join(
            f"{r['name']}: {r['value']}" for r in lab_results
        )

    prompt = f"""Write the "What You Have" section of a personalized health article for a patient diagnosed with: {diagnosis}

{lab_text}

Medical reference:
{context}

Write 3-4 paragraphs explaining directly to the patient:
- What this condition is, in simple everyday words
- What it means concretely for their body
- Why it happens (main causes)
- What their specific results mean (if lab results are provided)

{RULES}
"""
    return {
        "section": "What You Have",
        "content": generate_section(prompt),
        "image_keyword": f"{diagnosis} anatomy body",
        "sources": [c["url"] for c in chunks if c["url"]],
    }


def gen_how_it_works(medical_data: dict) -> dict:
    diagnosis = medical_data.get("diagnosis") or "your condition"

    chunks = retrieve(f"{diagnosis} mechanism physiology how it works", k=5)
    context = "\n\n".join(c["text"] for c in chunks)

    prompt = f"""Write the "How It Works" section of a personalized health article for a patient with: {diagnosis}

Medical reference:
{context}

Write 3-4 paragraphs explaining the biological mechanism of this condition directly to the patient.
Use analogies and simple language — as if explaining to someone with no medical background.
Example style: "Think of your pancreas like a factory. When everything works well, it produces just the right amount of insulin..."

{RULES}
"""
    return {
        "section": "How It Works",
        "content": generate_section(prompt),
        "image_keyword": f"{diagnosis} mechanism diagram biology",
        "sources": [c["url"] for c in chunks if c["url"]],
    }


def gen_how_to_treat(medical_data: dict) -> dict:
    diagnosis = medical_data.get("diagnosis") or "your condition"
    medications = medical_data.get("medications", [])
    recommendations = medical_data.get("recommendations", [])

    chunks = retrieve(f"{diagnosis} treatment therapy medication", k=5)
    context = "\n\n".join(c["text"] for c in chunks)

    meds_text = f"Prescribed medications: {', '.join(medications)}" if medications else ""
    reco_text = f"Doctor's recommendations: {', '.join(recommendations)}" if recommendations else ""

    prompt = f"""Write the "How To Treat It" section of a personalized health article for a patient with: {diagnosis}

{meds_text}
{reco_text}

Medical reference:
{context}

Write 3-4 paragraphs addressed directly to the patient covering:
- The main treatment approaches for this condition
- How their prescribed medications work, in simple words (if any)
- Lifestyle changes that will help them recover or manage the condition
- What improvements they can expect and on what timeline

Always remind them to follow their doctor's advice and never change doses on their own.

{RULES}
"""
    return {
        "section": "How To Treat It",
        "content": generate_section(prompt),
        "image_keyword": f"{diagnosis} treatment healthy lifestyle",
        "sources": [c["url"] for c in chunks if c["url"]],
    }


def gen_daily_life(medical_data: dict) -> dict:
    diagnosis = medical_data.get("diagnosis") or "your condition"

    chunks = retrieve(f"{diagnosis} daily life tips diet exercise patient advice", k=5)
    context = "\n\n".join(c["text"] for c in chunks)

    prompt = f"""Write the "Daily Life" section of a personalized health article for a patient with: {diagnosis}

Medical reference:
{context}

Write practical, actionable content addressed directly to the patient, organized around:
- Nutrition and diet
- Physical activity
- Sleep and stress management
- Monitoring and daily routine

Be specific and practical — not generic advice. Use short paragraphs or bullet points with brief explanations.

{RULES}
"""
    return {
        "section": "Daily Life",
        "content": generate_section(prompt),
        "image_keyword": f"healthy lifestyle {diagnosis} daily routine",
        "sources": [c["url"] for c in chunks if c["url"]],
    }


def gen_warning_signs(medical_data: dict) -> dict:
    diagnosis = medical_data.get("diagnosis") or "your condition"

    chunks = retrieve(f"{diagnosis} warning signs complications emergency when to see doctor", k=5)
    context = "\n\n".join(c["text"] for c in chunks)

    prompt = f"""Write the "Warning Signs" section of a personalized health article for a patient with: {diagnosis}

Medical reference:
{context}

Write a clear, calm (not alarmist) section addressed directly to the patient covering:
- Symptoms that mean things may be getting worse — when to call their doctor soon
- Emergency signs that require immediate medical attention
- Positive signs that show the treatment is working

Goal: empower the patient with knowledge, not scare them.

{RULES}
"""
    return {
        "section": "Warning Signs",
        "content": generate_section(prompt),
        "image_keyword": "doctor patient consultation medical",
        "sources": [c["url"] for c in chunks if c["url"]],
    }


# ── Main entry point ───────────────────────────────────────────────────────────

def generate_article_content(medical_data: dict) -> dict:
    print("Generating intro...")
    intro_data = gen_intro(medical_data)

    print("Generating 'What You Have'...")
    what_section = gen_what_you_have(medical_data)

    print("Generating 'How It Works'...")
    mechanism_section = gen_how_it_works(medical_data)

    print("Generating 'How To Treat It'...")
    treatment_section = gen_how_to_treat(medical_data)

    print("Generating 'Daily Life'...")
    daily_section = gen_daily_life(medical_data)

    print("Generating 'Warning Signs'...")
    warning_section = gen_warning_signs(medical_data)

    return {
        "title": intro_data["title"],
        "intro": intro_data["intro"],
        "patient_name": medical_data.get("patient_name"),
        "diagnosis": medical_data.get("diagnosis"),
        "sections": [what_section, mechanism_section, treatment_section, daily_section, warning_section],
        "image_keywords": {
            "hero": intro_data["image_keyword"],
            "what": what_section["image_keyword"],
            "mechanism": mechanism_section["image_keyword"],
            "treatment": treatment_section["image_keyword"],
            "daily": daily_section["image_keyword"],
            "warning": warning_section["image_keyword"],
        },
    }
