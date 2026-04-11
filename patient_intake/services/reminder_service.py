"""
Génération de rappels de prise de médicaments.
Logique partagée avec main.py — centralisée ici pour le module patient_intake.
"""

import re
from datetime import date, timedelta
from typing import Optional


FREQUENCY_MAP: dict[str, list[tuple[str, str]]] = {
    "once_daily":      [("21:00", "Soir")],
    "twice_daily":     [("09:00", "Matin"), ("21:00", "Soir")],
    "three_daily":     [("09:00", "Matin"), ("14:00", "Après-midi"), ("21:00", "Soir")],
    "four_daily":      [("09:00", "Matin"), ("13:00", "Midi"), ("17:00", "Après-midi"), ("21:00", "Soir")],
    "every_6h":        [("09:00", "Matin"), ("13:00", "Midi"), ("17:00", "Après-midi"), ("21:00", "Soir")],
    "every_8h":        [("09:00", "Matin"), ("15:00", "Après-midi"), ("21:00", "Soir")],
    "every_12h":       [("09:00", "Matin"), ("21:00", "Soir")],
    "morning":         [("09:00", "Matin")],
    "evening":         [("21:00", "Soir")],
    "noon":            [("13:00", "Midi")],
    "morning_evening": [("09:00", "Matin"), ("21:00", "Soir")],
    "before_meals":    [("09:00", "Avant petit-déjeuner"), ("12:30", "Avant déjeuner"), ("19:30", "Avant dîner")],
    "with_meals":      [("09:30", "Petit-déjeuner"), ("13:00", "Déjeuner"), ("20:00", "Dîner")],
    "after_meals":     [("10:00", "Après petit-déjeuner"), ("13:30", "Après déjeuner"), ("20:30", "Après dîner")],
    "as_needed":       [("21:00", "Si besoin")],
}

FREQUENCY_KEYWORDS: list[tuple[list[str], str]] = [
    (["every 6 hours", "toutes les 6h", "toutes les 6 heures"], "every_6h"),
    (["every 8 hours", "toutes les 8h", "toutes les 8 heures"], "every_8h"),
    (["every 12 hours", "toutes les 12h", "toutes les 12 heures"], "every_12h"),
    (["4 fois", "4x", "four times", "quatre fois"], "four_daily"),
    (["3 fois", "3x", "three times", "trois fois", "t.i.d"], "three_daily"),
    (["2 fois", "2x", "twice", "deux fois", "b.i.d"], "twice_daily"),
    (["avant les repas", "before meals", "avant chaque repas"], "before_meals"),
    (["pendant les repas", "with meals", "au cours des repas"], "with_meals"),
    (["après les repas", "after meals", "après chaque repas"], "after_meals"),
    (["matin et soir", "morning and evening"], "morning_evening"),
    (["au coucher", "le soir", "at bedtime", "soir"], "evening"),
    (["le matin", "morning", "matin"], "morning"),
    (["à midi", "noon", "midi"], "noon"),
    (["si besoin", "as needed", "au besoin", "prn"], "as_needed"),
    (["1 fois", "once daily", "une fois par jour"], "once_daily"),
]


def detect_frequency_key(frequency_text: str) -> str:
    normalized = frequency_text.lower().strip()
    for keywords, key in FREQUENCY_KEYWORDS:
        if any(kw in normalized for kw in keywords):
            return key
    return "once_daily"


def parse_duration_days(duration_text: Optional[str]) -> Optional[int]:
    if not duration_text:
        return None
    text = duration_text.lower()
    match = re.search(r"(\d+)\s*(jour|day|semaine|week|mois|month)", text)
    if not match:
        return None
    qty = int(match.group(1))
    unit = match.group(2)
    if unit.startswith(("semaine", "week")):
        return qty * 7
    if unit.startswith(("mois", "month")):
        return qty * 30
    return qty


def build_reminders(medications: list[dict]) -> list[dict]:
    """
    Génère les rappels à partir d'une liste de médicaments (dicts avec name, dosage, frequency, duration).
    Retourne une liste de dicts compatibles avec le schéma Reminder de main.py.
    """
    reminders: list[dict] = []
    today = date.today()

    for med in medications:
        freq_key = detect_frequency_key(med.get("frequency") or "")
        schedule = FREQUENCY_MAP.get(freq_key, FREQUENCY_MAP["once_daily"])

        duration_days = parse_duration_days(med.get("duration"))
        end_date = (today + timedelta(days=duration_days)).isoformat() if duration_days else None

        for slot_time, slot_label in schedule:
            dosage = med.get("dosage") or ""
            reminders.append({
                "medication_name": med.get("name", ""),
                "dosage": dosage or None,
                "time": slot_time,
                "label": f"{med.get('name', '')}{' ' + dosage if dosage else ''} — {slot_label}",
                "recurrence": freq_key,
                "start_date": today.isoformat(),
                "end_date": end_date,
            })

    reminders.sort(key=lambda r: r["time"])
    return reminders
