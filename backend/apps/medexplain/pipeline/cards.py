"""
Dynamic data card renderer using Pillow.

Produces 1280×720 JPEG cards for data-driven visual scenes
(medications, warnings, follow-up, etc.).
"""
from __future__ import annotations

import os
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1280
HEIGHT = 720

# --------------------------------------------------------------------------
# Palette — white background
# --------------------------------------------------------------------------
BG = (255, 255, 255)
DIVIDER = (210, 220, 235)
TEXT = (20, 30, 55)
WHITE = (255, 255, 255)
LIGHT = (65, 90, 130)
MUTED = (150, 165, 185)
BLUE = (30, 120, 255)
GREEN = (25, 175, 85)
ORANGE = (235, 130, 20)
RED = (220, 45, 45)

TOP_STRIPE_H = 6
MARGIN = 80
TITLE_Y = 48
TITLE_SIZE = 42
DIVIDER_Y = 108


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = (
        [
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        if bold
        else [
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
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


def _trunc(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"


def _base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (WIDTH, TOP_STRIPE_H)], fill=BLUE)
    return img, draw


def _title(draw: ImageDraw.ImageDraw, text: str) -> int:
    """Draw title + divider line. Returns y offset after the block."""
    font = _load_font(TITLE_SIZE, bold=True)
    draw.text((MARGIN, TITLE_Y), text, font=font, fill=TEXT)
    draw.rectangle([(MARGIN, DIVIDER_Y), (WIDTH - MARGIN, DIVIDER_Y + 3)], fill=DIVIDER)
    return DIVIDER_Y + 22


def _dot(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple) -> None:
    r = 7
    draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=color)


def _badge(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, color: tuple) -> int:
    """Draw a small coloured badge. Returns x offset after the badge."""
    font = _load_font(17, bold=True)
    pad_x, pad_y = 10, 5
    bbox = draw.textbbox((0, 0), label, font=font)
    w = bbox[2] - bbox[0] + pad_x * 2
    h = bbox[3] - bbox[1] + pad_y * 2
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=4, fill=color)
    draw.text((x + pad_x, y + pad_y), label, font=font, fill=WHITE)
    return x + w + 12


# --------------------------------------------------------------------------
# Card renderers — each saves to output_path as JPEG
# --------------------------------------------------------------------------

def render_medications_card(medications: list, output_path: str) -> None:
    img, draw = _base()
    y = _title(draw, "Vos Médicaments")

    name_font = _load_font(28, bold=True)
    detail_font = _load_font(23)

    for med in medications[:4]:
        if y > HEIGHT - 90:
            break
        _dot(draw, MARGIN + 7, y + 14, BLUE)
        name = med.name + (f"  ({med.brand_name})" if med.brand_name else "")
        draw.text((MARGIN + 24, y), _trunc(name, 52), font=name_font, fill=TEXT)
        y += 36
        detail = f"{med.dosage}  ·  {med.frequency}  ·  {med.timing}"
        draw.text((MARGIN + 24, y), _trunc(detail, 72), font=detail_font, fill=LIGHT)
        y += 44

    extra = len(medications) - 4
    if extra > 0:
        draw.text(
            (MARGIN, y),
            f"+ {extra} autre{'s' if extra > 1 else ''} médicament{'s' if extra > 1 else ''}",
            font=_load_font(20),
            fill=MUTED,
        )

    img.save(output_path, "JPEG", quality=95)


def render_warnings_card(warnings: list, output_path: str) -> None:
    img, draw = _base()
    y = _title(draw, "Points d'Attention Importants")

    text_font = _load_font(26)
    colors = {"high": RED, "medium": ORANGE, "low": GREEN}
    labels = {"high": "IMPORTANT", "medium": "ATTENTION", "low": "INFO"}

    for w in warnings[:5]:
        if y > HEIGHT - 80:
            break
        color = colors.get(w.severity, ORANGE)
        label = labels.get(w.severity, "NOTE")
        x_after = _badge(draw, MARGIN, y + 2, label, color)
        draw.text((x_after, y), _trunc(w.warning, 68), font=text_font, fill=LIGHT)
        y += 52

    img.save(output_path, "JPEG", quality=95)


def render_warning_signs_card(warning_signs: list, output_path: str) -> None:
    img, draw = _base()
    y = _title(draw, "Signes d'Alerte à Surveiller")

    sign_font = _load_font(27, bold=True)
    action_font = _load_font(22)
    urgency_colors = {"urgent": RED, "medium": ORANGE, "low": GREEN}

    for ws in warning_signs[:4]:
        if y > HEIGHT - 90:
            break
        color = urgency_colors.get(ws.urgency, ORANGE)
        _dot(draw, MARGIN + 7, y + 14, color)
        draw.text((MARGIN + 24, y), _trunc(ws.sign, 58), font=sign_font, fill=TEXT)
        y += 36
        draw.text((MARGIN + 24, y), _trunc(f"→  {ws.action}", 70), font=action_font, fill=LIGHT)
        y += 44

    img.save(output_path, "JPEG", quality=95)


def render_follow_up_card(follow_up, output_path: str) -> None:
    img, draw = _base()
    y = _title(draw, "Votre Suivi Médical")

    label_font = _load_font(22)
    value_font = _load_font(28, bold=True)
    small_font = _load_font(22)

    fields = [
        ("Prochain rendez-vous", follow_up.next_appointment),
        ("Spécialiste", follow_up.specialist),
        ("À apporter", follow_up.what_to_bring),
    ]

    for label, value in fields:
        if y > HEIGHT - 100:
            break
        draw.text((MARGIN, y), label, font=label_font, fill=MUTED)
        y += 28
        draw.text((MARGIN, y), _trunc(str(value), 62), font=value_font, fill=TEXT)
        y += 46

    if follow_up.additional_referrals and y < HEIGHT - 80:
        draw.text((MARGIN, y), "Autres consultations", font=label_font, fill=MUTED)
        y += 28
        for ref in follow_up.additional_referrals[:3]:
            draw.text((MARGIN, y), f"• {_trunc(ref, 60)}", font=small_font, fill=LIGHT)
            y += 30

    img.save(output_path, "JPEG", quality=95)


def render_precautions_card(precautions: List[str], output_path: str) -> None:
    img, draw = _base()
    y = _title(draw, "Précautions au Quotidien")

    item_font = _load_font(27)

    for prec in precautions[:6]:
        if y > HEIGHT - 80:
            break
        _dot(draw, MARGIN + 7, y + 14, GREEN)
        draw.text((MARGIN + 24, y), _trunc(prec, 70), font=item_font, fill=LIGHT)
        y += 48

    img.save(output_path, "JPEG", quality=95)


def render_test_results_card(test_results: list, output_path: str) -> None:
    img, draw = _base()
    y = _title(draw, "Vos Résultats d'Examens")

    name_font = _load_font(25, bold=True)
    result_font = _load_font(24)

    for test in test_results[:5]:
        if y > HEIGHT - 90:
            break
        draw.text((MARGIN, y), _trunc(test.plain_name, 55), font=name_font, fill=TEXT)
        y += 32
        draw.text((MARGIN, y), _trunc(test.result_plain, 72), font=result_font, fill=LIGHT)
        y += 36
        draw.rectangle([(MARGIN, y), (WIDTH - MARGIN, y + 1)], fill=DIVIDER)
        y += 16

    img.save(output_path, "JPEG", quality=95)


def render_key_concepts_card(what_is_happening, output_path: str) -> None:
    """
    Render a "How it works" card for video 1 visual scenes.

    Shows the overall plain-language mechanism + up to 3 key medical concepts,
    each with its clinical term and patient-facing explanation.
    """
    INDIGO = (60, 80, 200)
    INDIGO_LIGHT = (235, 238, 255)
    INDIGO_MUTED = (100, 115, 200)

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    # Top stripe in indigo instead of blue to visually differentiate from treatment cards
    draw.rectangle([(0, 0), (WIDTH, 6)], fill=INDIGO)

    # Title block
    title_font = _load_font(TITLE_SIZE, bold=True)
    draw.text((MARGIN, TITLE_Y), "Comment ça fonctionne", font=title_font, fill=TEXT)
    draw.rectangle([(MARGIN, DIVIDER_Y), (WIDTH - MARGIN, DIVIDER_Y + 3)], fill=DIVIDER)
    y = DIVIDER_Y + 22

    # Overall mechanism (the "plain_language" summary from WhatIsHappeningInBody)
    if what_is_happening.plain_language:
        summary_font = _load_font(24)
        summary_text = _trunc(what_is_happening.plain_language, 110)
        # Word-wrap into two lines max
        words = summary_text.split()
        line1, line2 = [], []
        for word in words:
            if len(" ".join(line1 + [word])) <= 58:
                line1.append(word)
            else:
                line2.append(word)
        draw.text((MARGIN, y), " ".join(line1), font=summary_font, fill=LIGHT)
        y += 30
        if line2:
            draw.text((MARGIN, y), " ".join(line2), font=summary_font, fill=LIGHT)
            y += 30
        y += 10
        draw.rectangle([(MARGIN, y), (WIDTH - MARGIN, y + 1)], fill=DIVIDER)
        y += 18

    concepts = what_is_happening.key_concepts or []
    term_font = _load_font(26, bold=True)
    plain_font = _load_font(22)
    badge_font = _load_font(15, bold=True)

    for concept in concepts[:3]:
        if y > HEIGHT - 100:
            break

        # Indigo badge pill behind the clinical term
        term_label = _trunc(concept.term, 38)
        bbox = draw.textbbox((0, 0), term_label, font=term_font)
        term_w = bbox[2] - bbox[0]
        pill_pad = 12
        pill_h = 38
        draw.rounded_rectangle(
            [(MARGIN, y), (MARGIN + term_w + pill_pad * 2, y + pill_h)],
            radius=8,
            fill=INDIGO_LIGHT,
        )
        draw.text((MARGIN + pill_pad, y + 6), term_label, font=term_font, fill=INDIGO)
        y += pill_h + 6

        # Plain-language explanation beneath the pill
        plain_text = _trunc(concept.plain_language, 80)
        draw.text((MARGIN, y), plain_text, font=plain_font, fill=LIGHT)
        y += 32

        # Thin separator between concepts
        draw.rectangle([(MARGIN, y), (WIDTH - MARGIN, y + 1)], fill=DIVIDER)
        y += 14

    img.save(output_path, "JPEG", quality=95)


def render_diagnosis_card(diagnosis, severity, output_path: str) -> None:
    """
    Render a diagnosis summary card for video 1 visual scenes.
    Shows the clinical term, patient explanation, and severity badge.
    """
    PURPLE = (120, 50, 210)
    PURPLE_LIGHT = (240, 232, 255)

    severity_colors = {
        "mild": GREEN,
        "moderate": ORANGE,
        "severe": RED,
    }
    severity_labels = {
        "mild": "LÉGER",
        "moderate": "MODÉRÉ",
        "severe": "SÉVÈRE",
    }

    img, draw = _base()
    y = _title(draw, "Votre Diagnostic")

    term_font = _load_font(36, bold=True)
    explanation_font = _load_font(24)

    # Clinical term
    draw.text((MARGIN, y), _trunc(diagnosis.clinical_term, 40), font=term_font, fill=TEXT)
    y += 52

    # Severity badge
    sev_level = (severity.level or "mild").lower()
    sev_color = severity_colors.get(sev_level, ORANGE)
    sev_label = severity_labels.get(sev_level, sev_level.upper())
    x_after = _badge(draw, MARGIN, y, sev_label, sev_color)
    y += 36

    # Thin divider
    draw.rectangle([(MARGIN, y), (WIDTH - MARGIN, y + 2)], fill=DIVIDER)
    y += 18

    # Patient explanation (word-wrapped)
    explanation = diagnosis.patient_explanation or diagnosis.plain_language or ""
    words = explanation.split()
    line: list[str] = []
    for word in words:
        if len(" ".join(line + [word])) <= 70:
            line.append(word)
        else:
            if y > HEIGHT - 40:
                break
            draw.text((MARGIN, y), " ".join(line), font=explanation_font, fill=LIGHT)
            y += 32
            line = [word]
    if line and y <= HEIGHT - 40:
        draw.text((MARGIN, y), " ".join(line), font=explanation_font, fill=LIGHT)

    img.save(output_path, "JPEG", quality=95)
