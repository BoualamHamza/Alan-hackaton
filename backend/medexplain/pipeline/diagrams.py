"""
Pillow-based diagram renderer for avatar scene overlays.

Produces 560×720 PNG panels placed on the left of a 1280×720 split-screen
(avatar occupies the right 720×720 square).

Three diagram types:
  - severity   : disease progression gauge + current stage
  - risk_factors : identified risk factors list
  - treatment  : medication summary + next appointment
"""
from __future__ import annotations

import os
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

PANEL_W = 560
PANEL_H = 720
MARGIN = 38

# Shared palette (matches cards.py) — white background
BG = (255, 255, 255)
DIVIDER = (210, 220, 235)
TEXT = (20, 30, 55)
LIGHT = (65, 90, 130)
MUTED = (150, 165, 185)
BLUE = (30, 120, 255)
GREEN = (25, 175, 85)
ORANGE = (235, 130, 20)
RED = (220, 45, 45)
YELLOW = (220, 170, 0)

# Severity level → gauge fill ratio + colour
_SEVERITY_MAP = {
    "mild":     (0.22, GREEN),
    "moderate": (0.55, ORANGE),
    "severe":   (0.88, RED),
}
_SEVERITY_LABELS = {
    "mild": "LÉGER",
    "moderate": "MODÉRÉ",
    "severe": "SÉVÈRE",
}


# ---------------------------------------------------------------------------
# Font helpers (identical pattern to cards.py)
# ---------------------------------------------------------------------------

def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = (
        [
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        if bold
        else [
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    )
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _trunc(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def _base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (PANEL_W, PANEL_H), BG)
    draw = ImageDraw.Draw(img)
    # Top accent stripe
    draw.rectangle([(0, 0), (PANEL_W, 5)], fill=BLUE)
    # Right border separating diagram from avatar
    draw.rectangle([(PANEL_W - 3, 0), (PANEL_W, PANEL_H)], fill=DIVIDER)
    return img, draw


def _section_title(draw: ImageDraw.ImageDraw, text: str, y: int) -> int:
    font = _load_font(13, bold=True)
    draw.text((MARGIN, y), text.upper(), font=font, fill=MUTED)
    y += 22
    draw.rectangle([(MARGIN, y), (PANEL_W - MARGIN, y + 1)], fill=DIVIDER)
    return y + 12


# ---------------------------------------------------------------------------
# Diagram 1 — Disease severity gauge
# ---------------------------------------------------------------------------

def render_severity_diagram(
    diagnosis_plain: str,
    severity_level: str,  # "mild" | "moderate" | "severe"
    severity_plain: str,
    output_path: str,
) -> None:
    """
    Shows a horizontal severity gauge with the patient's current stage
    highlighted, plus a brief plain-language note below.
    """
    img, draw = _base()

    # --- Title ---
    title_font = _load_font(22, bold=True)
    sub_font = _load_font(14)
    y = 30
    draw.text((MARGIN, y), _trunc(diagnosis_plain, 28), font=title_font, fill=TEXT)
    y += 34

    # --- Gauge ---
    y = _section_title(draw, "Stade de la maladie", y + 10)

    fill_ratio, gauge_color = _SEVERITY_MAP.get(severity_level, (0.55, ORANGE))
    label = _SEVERITY_LABELS.get(severity_level, severity_level.upper())

    gauge_x = MARGIN
    gauge_y = y + 20
    gauge_w = PANEL_W - MARGIN * 2
    gauge_h = 18
    fill_w = int(gauge_w * fill_ratio)

    # Background track
    draw.rounded_rectangle(
        [(gauge_x, gauge_y), (gauge_x + gauge_w, gauge_y + gauge_h)],
        radius=9, fill=DIVIDER,
    )
    # Fill
    if fill_w > 18:
        draw.rounded_rectangle(
            [(gauge_x, gauge_y), (gauge_x + fill_w, gauge_y + gauge_h)],
            radius=9, fill=gauge_color,
        )

    y = gauge_y + gauge_h + 10

    # Labels below gauge
    label_font = _load_font(13)
    draw.text((gauge_x, y), "Léger", font=label_font, fill=MUTED)
    draw.text((gauge_x + gauge_w - 40, y), "Sévère", font=label_font, fill=MUTED)
    y += 22

    # Current level badge
    badge_font = _load_font(18, bold=True)
    badge_text = f"Stade actuel : {label}"
    draw.text((MARGIN, y), badge_text, font=badge_font, fill=gauge_color)
    y += 36

    # --- Divider + plain language note ---
    y = _section_title(draw, "Ce que cela signifie", y + 8)

    note_font = _load_font(16)
    words = severity_plain.split()
    line, lines = [], []
    for word in words:
        test = " ".join(line + [word])
        if _text_width(draw, test, note_font) > PANEL_W - MARGIN * 2:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))

    for text_line in lines[:6]:
        if y > PANEL_H - 60:
            break
        draw.text((MARGIN, y), text_line, font=note_font, fill=TEXT)
        y += 22

    # --- Footer ---
    _draw_footer(draw, img)
    img.save(output_path, "PNG")


# ---------------------------------------------------------------------------
# Diagram 2 — Risk factors
# ---------------------------------------------------------------------------

def render_risk_factors_diagram(
    risk_factors: List[str],
    patient_note: str,
    output_path: str,
) -> None:
    """
    Lists identified risk factors with colour-coded dots,
    then adds a brief patient-facing explanatory note.
    """
    img, draw = _base()

    title_font = _load_font(22, bold=True)
    y = 30
    draw.text((MARGIN, y), "Facteurs de risque", font=title_font, fill=TEXT)
    y += 44

    y = _section_title(draw, "Identifiés pour vous", y)

    item_font = _load_font(17)
    dot_colors = [RED, ORANGE, YELLOW, BLUE, GREEN]

    for i, factor in enumerate(risk_factors[:7]):
        if y > PANEL_H - 140:
            break
        color = dot_colors[i % len(dot_colors)]
        cx, cy = MARGIN + 7, y + 10
        draw.ellipse([(cx - 7, cy - 7), (cx + 7, cy + 7)], fill=color)
        draw.text((MARGIN + 22, y), _trunc(factor, 34), font=item_font, fill=TEXT)
        y += 30

    # --- Note ---
    y = _section_title(draw, "Explication", y + 12)
    note_font = _load_font(15)
    words = patient_note.split()
    line, lines = [], []
    for word in words:
        test = " ".join(line + [word])
        if _text_width(draw, test, note_font) > PANEL_W - MARGIN * 2:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))

    for text_line in lines[:5]:
        if y > PANEL_H - 55:
            break
        draw.text((MARGIN, y), text_line, font=note_font, fill=TEXT)
        y += 20

    _draw_footer(draw, img)
    img.save(output_path, "PNG")


# ---------------------------------------------------------------------------
# Diagram 3 — Treatment summary
# ---------------------------------------------------------------------------

def render_treatment_diagram(
    medications: list,
    next_appointment: str,
    output_path: str,
) -> None:
    """
    Lists the prescribed medications with dosage/frequency,
    then shows the next follow-up appointment.
    """
    img, draw = _base()

    title_font = _load_font(22, bold=True)
    y = 30
    draw.text((MARGIN, y), "Votre traitement", font=title_font, fill=TEXT)
    y += 44

    y = _section_title(draw, "Médicaments prescrits", y)

    name_font = _load_font(17, bold=True)
    detail_font = _load_font(14)

    for med in medications[:4]:
        if y > PANEL_H - 150:
            break
        # Pill icon via unicode bullet
        draw.ellipse([(MARGIN, y + 6), (MARGIN + 10, y + 16)], fill=BLUE)
        draw.text((MARGIN + 18, y), _trunc(med.name, 26), font=name_font, fill=TEXT)
        y += 24
        dose_text = f"{med.dosage}  ·  {med.frequency}"
        draw.text((MARGIN + 18, y), _trunc(dose_text, 32), font=detail_font, fill=LIGHT)  # LIGHT is dark on white
        y += 26

    # --- Next appointment ---
    y = _section_title(draw, "Prochain rendez-vous", y + 10)
    appt_font = _load_font(18, bold=True)
    draw.text((MARGIN, y), _trunc(next_appointment, 28), font=appt_font, fill=GREEN)

    _draw_footer(draw, img)
    img.save(output_path, "PNG")


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def _text_width(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _draw_footer(draw: ImageDraw.ImageDraw, img: Image.Image) -> None:
    font = _load_font(12)
    text = "MedExplain"
    draw.text((MARGIN, PANEL_H - 22), text, font=font, fill=MUTED)
