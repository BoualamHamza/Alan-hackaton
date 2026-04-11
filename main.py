"""
Medical Prescription Analyzer API
Hackathon Médical - Plateforme de compréhension des ordonnances
"""

import base64
import json
import os
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta
from typing import Optional

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from patient_intake.models.database import init_db
from patient_intake.routers.intake import router as intake_router
from wearable.router import router as wearable_router

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
VISION_MODEL = "mistral-small-latest"

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "application/pdf"}

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class Medication(BaseModel):
    name: str = Field(..., description="Nom du médicament / Medication name")
    dosage: str = Field(..., description="Dosage (ex: 500mg, 1 comprimé)")
    frequency: str = Field(..., description="Fréquence (ex: 3 fois par jour, matin et soir)")
    duration: Optional[str] = Field(None, description="Durée du traitement (ex: 7 jours)")
    instructions: Optional[str] = Field(None, description="Instructions spéciales (ex: à prendre pendant les repas)")
    side_effects: Optional[list[str]] = Field(default_factory=list, description="Effets secondaires mentionnés")


class Reminder(BaseModel):
    medication_name: str
    dosage: str
    time: str = Field(..., description="Heure du rappel au format HH:MM")
    label: str = Field(..., description="Label lisible (ex: 'Doliprane 500mg - Matin')")
    recurrence: str = Field(..., description="Récurrence (ex: daily, every_8h)")
    start_date: Optional[date] = Field(None)
    end_date: Optional[date] = Field(None)


class PrescriptionResult(BaseModel):
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    date: Optional[str] = None
    medications: list[Medication] = Field(default_factory=list)
    reminders: list[Reminder] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    model: str
    api_key_configured: bool


# ---------------------------------------------------------------------------
# Frequency → Schedule Mapping
# ---------------------------------------------------------------------------

# Each entry: list of (HH:MM, human label suffix)
FREQUENCY_MAP: dict[str, list[tuple[str, str]]] = {
    # Une fois par jour — soir par défaut (sécurité photosensibilité)
    "once_daily": [("21:00", "Soir")],
    # Deux fois par jour
    "twice_daily": [("09:00", "Matin"), ("21:00", "Soir")],
    # Trois fois par jour
    "three_daily": [("09:00", "Matin"), ("14:00", "Après-midi"), ("21:00", "Soir")],
    # Quatre fois par jour
    "four_daily": [("09:00", "Matin"), ("13:00", "Midi"), ("17:00", "Après-midi"), ("21:00", "Soir")],
    # Toutes les 8 heures — espacé sur la journée éveillée
    "every_8h": [("09:00", "Matin"), ("15:00", "Après-midi"), ("21:00", "Soir")],
    # Toutes les 12 heures
    "every_12h": [("09:00", "Matin"), ("21:00", "Soir")],
    # Toutes les 6 heures — 4 prises sur la journée éveillée
    "every_6h": [("09:00", "Matin"), ("13:00", "Midi"), ("17:00", "Après-midi"), ("21:00", "Soir")],
    # Matin seulement
    "morning": [("09:00", "Matin")],
    # Soir seulement / au coucher
    "evening": [("21:00", "Coucher")],
    # Midi seulement
    "noon": [("13:00", "Midi")],
    # Matin et soir
    "morning_evening": [("09:00", "Matin"), ("21:00", "Soir")],
    # Avant les repas (3 fois)
    "before_meals": [("09:00", "Avant petit-déjeuner"), ("12:30", "Avant déjeuner"), ("19:30", "Avant dîner")],
    # Pendant les repas (3 fois)
    "with_meals": [("09:30", "Petit-déjeuner"), ("13:00", "Déjeuner"), ("20:00", "Dîner")],
    # Après les repas (3 fois)
    "after_meals": [("10:00", "Après petit-déjeuner"), ("13:30", "Après déjeuner"), ("20:30", "Après dîner")],
    # Au besoin
    "as_needed": [("21:00", "Si besoin")],
}

# Keywords to detect frequency from the extracted text
FREQUENCY_KEYWORDS: list[tuple[list[str], str]] = [
    # Most specific first to avoid false matches
    (["every 6 hours", "toutes les 6h", "toutes les 6 heures", "6h"], "every_6h"),
    (["every 8 hours", "toutes les 8h", "toutes les 8 heures", "8h"], "every_8h"),
    (["every 12 hours", "toutes les 12h", "toutes les 12 heures", "12h"], "every_12h"),
    (["4 fois", "4x", "four times", "quatre fois"], "four_daily"),
    (["3 fois", "3x", "three times", "trois fois", "ter in die", "t.i.d"], "three_daily"),
    (["2 fois", "2x", "two times", "twice", "deux fois", "bis in die", "b.i.d"], "twice_daily"),
    (["avant les repas", "before meals", "avant chaque repas"], "before_meals"),
    (["pendant les repas", "with meals", "au cours des repas", "during meals"], "with_meals"),
    (["après les repas", "after meals", "après chaque repas"], "after_meals"),
    (["matin et soir", "morning and evening", "morning and night"], "morning_evening"),
    (["au coucher", "le soir", "au soir", "at bedtime", "bedtime", "evening", "soir"], "evening"),
    (["le matin", "au matin", "morning", "matin", "semel in die", "s.i.d"], "morning"),
    (["à midi", "au déjeuner", "at noon", "noon", "midi"], "noon"),
    (["si besoin", "as needed", "as required", "au besoin", "prn"], "as_needed"),
    (["1 fois", "once daily", "une fois", "once a day", "une fois par jour"], "once_daily"),
]


def detect_frequency_key(frequency_text: str) -> str:
    """Map a free-text frequency description to a FREQUENCY_MAP key."""
    normalized = frequency_text.lower().strip()
    for keywords, key in FREQUENCY_KEYWORDS:
        if any(kw in normalized for kw in keywords):
            return key
    # Default: soir (évite la photosensibilité quand l'heure n'est pas précisée)
    return "once_daily"


def parse_duration_days(duration_text: Optional[str]) -> Optional[int]:
    """Extract number of days from duration string. Returns None if unparseable."""
    if not duration_text:
        return None
    text = duration_text.lower()
    import re
    # "7 jours", "7 days", "1 semaine" / "1 week", "1 mois" / "1 month"
    match = re.search(r"(\d+)\s*(jour|day|semaine|week|mois|month)", text)
    if not match:
        return None
    qty = int(match.group(1))
    unit = match.group(2)
    if unit.startswith(("semaine", "week")):
        return qty * 7
    if unit.startswith(("mois", "month")):
        return qty * 30
    return qty  # jours / days


def build_reminders(medications: list[Medication]) -> list[Reminder]:
    """Generate concrete reminder schedules from a list of medications."""
    reminders: list[Reminder] = []
    today = date.today()

    for med in medications:
        freq_key = detect_frequency_key(med.frequency)
        schedule = FREQUENCY_MAP.get(freq_key, FREQUENCY_MAP["once_daily"])

        # Compute end_date from duration
        duration_days = parse_duration_days(med.duration)
        end_date = today + timedelta(days=duration_days) if duration_days else None

        for slot_time, slot_label in schedule:
            reminders.append(
                Reminder(
                    medication_name=med.name,
                    dosage=med.dosage,
                    time=slot_time,
                    label=f"{med.name} {med.dosage} — {slot_label}",
                    recurrence=freq_key,
                    start_date=today,
                    end_date=end_date,
                )
            )

    # Sort reminders by time of day
    reminders.sort(key=lambda r: r.time)
    return reminders


# ---------------------------------------------------------------------------
# Mistral Vision API
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a medical assistant specialized in reading and analyzing medical prescriptions.
Your task is to extract structured information from the provided prescription document.

The prescription may be in French or English. Extract all information accurately.

You MUST return a valid JSON object with EXACTLY this structure:
{
  "patient_name": "string or null",
  "doctor_name": "string or null",
  "date": "string or null (e.g. '2024-03-15')",
  "medications": [
    {
      "name": "medication name",
      "dosage": "dosage (e.g. '500mg', '1 tablet')",
      "frequency": "frequency in natural language (e.g. '3 fois par jour', 'twice daily', 'every 8 hours')",
      "duration": "treatment duration (e.g. '7 jours', '2 weeks') or null",
      "instructions": "special instructions (e.g. 'à prendre pendant les repas') or null",
      "side_effects": ["list of mentioned side effects or empty array"]
    }
  ]
}

Rules:
- If the document is NOT a medical prescription, return: {"error": "not_a_prescription"}
- Extract ALL medications listed on the prescription
- Keep frequency descriptions in their original language
- If a field cannot be determined, use null
- Do NOT invent information not present in the document
"""


async def call_mistral_vision(file_content: bytes, mime_type: str) -> dict:
    """Send a document to Mistral vision API and return parsed JSON."""
    if not MISTRAL_API_KEY:
        raise HTTPException(status_code=500, detail="MISTRAL_API_KEY not configured")

    # Encode file to base64
    b64_content = base64.b64encode(file_content).decode("utf-8")

    # Build the message content depending on file type
    if mime_type == "application/pdf":
        # Mistral accepts PDF as a document_url with base64
        user_content = [
            {
                "type": "text",
                "text": "Please analyze this medical prescription and extract all information.",
            },
            {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{b64_content}",
            },
        ]
    else:
        # Image (JPEG or PNG)
        user_content = [
            {
                "type": "text",
                "text": "Please analyze this medical prescription and extract all information.",
            },
            {
                "type": "image_url",
                "image_url": f"data:{mime_type};base64,{b64_content}",
            },
        ]

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,  # Low temperature for factual extraction
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                MISTRAL_API_URL,
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Mistral API timeout — please retry")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Cannot reach Mistral API: {str(e)}")

    if response.status_code == 401:
        raise HTTPException(status_code=500, detail="Invalid Mistral API key")
    if response.status_code == 429:
        raise HTTPException(status_code=429, detail="Mistral API rate limit reached — please retry later")
    if response.status_code >= 500:
        raise HTTPException(status_code=502, detail=f"Mistral API error: {response.status_code}")
    if not response.is_success:
        raise HTTPException(status_code=502, detail=f"Mistral API returned {response.status_code}: {response.text}")

    try:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=502, detail=f"Failed to parse Mistral response: {str(e)}")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Medical Prescription Analyzer",
    description="Analyse les ordonnances médicales et génère des rappels de prise de médicaments.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intake_router)
app.include_router(wearable_router)


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """Vérifie que le service est opérationnel."""
    return HealthResponse(
        status="ok",
        model=VISION_MODEL,
        api_key_configured=bool(MISTRAL_API_KEY),
    )


@app.post("/analyze-prescription", response_model=PrescriptionResult, tags=["Prescription"])
async def analyze_prescription(file: UploadFile = File(..., description="Image (JPG/PNG) ou PDF de l'ordonnance")):
    """
    Analyse une ordonnance médicale et retourne les médicaments extraits
    ainsi qu'une liste de rappels de prise générés automatiquement.
    """
    # --- Validate file type ---
    content_type = file.content_type or ""
    # Some clients send 'image/jpg' instead of 'image/jpeg'
    if content_type == "image/jpg":
        content_type = "image/jpeg"

    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Format non supporté: '{content_type}'. Formats acceptés: JPG, PNG, PDF.",
        )

    # --- Read file content ---
    file_content = await file.read()
    if not file_content:
        raise HTTPException(status_code=400, detail="Le fichier est vide.")

    # Limit to 10 MB to avoid Mistral payload issues
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 10 MB).")

    # --- Call Mistral Vision API ---
    extracted = await call_mistral_vision(file_content, content_type)

    # --- Handle "not a prescription" response ---
    if extracted.get("error") == "not_a_prescription":
        raise HTTPException(
            status_code=422,
            detail="Le document fourni ne semble pas être une ordonnance médicale.",
        )

    # --- Parse medications ---
    raw_medications = extracted.get("medications", [])
    if not raw_medications:
        raise HTTPException(
            status_code=422,
            detail="Aucun médicament détecté dans l'ordonnance.",
        )

    try:
        medications = [Medication(**med) for med in raw_medications]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Données médicaments invalides retournées par Mistral: {str(e)}")

    # --- Generate reminders ---
    reminders = build_reminders(medications)

    return PrescriptionResult(
        patient_name=extracted.get("patient_name"),
        doctor_name=extracted.get("doctor_name"),
        date=extracted.get("date"),
        medications=medications,
        reminders=reminders,
    )


# ---------------------------------------------------------------------------
# Calendar Export (.ics)
# ---------------------------------------------------------------------------

class CalendarExportRequest(BaseModel):
    reminders: list[Reminder]
    medications: list[Medication] = Field(default_factory=list)


def generate_ics(reminders: list[Reminder], medications: list[Medication]) -> str:
    """Generate an iCalendar (.ics) file from a list of reminders."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MedReminder//HackathonMedical//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Rappels Médicaments",
    ]

    med_lookup = {m.name: m for m in medications}
    today = date.today()

    for i, reminder in enumerate(reminders):
        hour, minute = reminder.time.split(":")
        start = reminder.start_date or today
        dtstart = f"{start.strftime('%Y%m%d')}T{hour}{minute}00"

        rrule = "FREQ=DAILY"
        if reminder.end_date:
            rrule += f";UNTIL={reminder.end_date.strftime('%Y%m%d')}T235959Z"

        # Build human-readable description
        med = med_lookup.get(reminder.medication_name)
        desc_parts = [f"Dosage: {reminder.dosage}"]
        if med and med.instructions:
            desc_parts.append(f"Instructions: {med.instructions}")
        if med and med.side_effects:
            desc_parts.append(f"Effets secondaires: {', '.join(med.side_effects)}")
        description = "\\n".join(desc_parts)

        uid_base = reminder.medication_name.replace(" ", "-")[:30]
        uid = f"med-{i}-{uid_base}-{start.strftime('%Y%m%d')}@medreminder"

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART:{dtstart}",
            "DURATION:PT15M",
            f"RRULE:{rrule}",
            f"SUMMARY:{reminder.label}",
            f"DESCRIPTION:{description}",
            # Alarm: notification at the exact reminder time
            "BEGIN:VALARM",
            "TRIGGER:-PT0M",
            "ACTION:DISPLAY",
            "DESCRIPTION:Rappel médicament",
            "END:VALARM",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


@app.post("/export-calendar", tags=["Prescription"])
async def export_calendar(data: CalendarExportRequest):
    """Génère un fichier .ics importable dans Google Calendar, Apple Calendar, etc."""
    ics_content = generate_ics(data.reminders, data.medications)
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=mes-medicaments.ics"},
    )
