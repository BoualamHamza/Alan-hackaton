"""
Step 5 — HTML article renderer.
Takes the generated article content + images and produces
a clean, self-contained HTML file inspired by WHOOP health articles.
Medical professional color palette: blues, teals, whites.
"""

import base64
import re
import os
from pathlib import Path
from datetime import date

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Clean SVG icons — no emojis, professional medical style
SECTION_ICONS = {
    "What You Have":   '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1565A8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
    "How It Works":    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1565A8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>',
    "How To Treat It": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1565A8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/><line x1="12" y1="14" x2="12" y2="18"/><line x1="10" y1="16" x2="14" y2="16"/></svg>',
    "Daily Life":      '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1565A8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "Warning Signs":   '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1565A8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
}

MONTHS_EN = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}


def format_date_en(d: date) -> str:
    return f"{MONTHS_EN[d.month]} {d.day}, {d.year}"


def markdown_to_html(text: str) -> str:
    """Converts basic markdown to HTML."""
    # Remove horizontal rules
    text = re.sub(r'\n?---+\n?', '', text)

    # Convert ### headings
    text = re.sub(r'### (.+)', r'<h3>\1</h3>', text)
    text = re.sub(r'## (.+)', r'<h3>\1</h3>', text)

    # Convert **bold**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # Convert *italic*
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    # Convert bullet lists
    lines = text.split('\n')
    html_lines = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{stripped[2:]}</li>')
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if stripped:
                html_lines.append(f'<p>{stripped}</p>')
            else:
                html_lines.append('')
    if in_list:
        html_lines.append('</ul>')

    return '\n'.join(html_lines)


def image_to_base64(filepath: str) -> str | None:
    if not filepath or not os.path.exists(filepath):
        return None
    with open(filepath, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{data}"


def render_section(section: dict, image_path: str | None, index: int) -> str:
    title = section["section"]
    content = markdown_to_html(section["content"])
    icon = SECTION_ICONS.get(title, "📋")
    img_b64 = image_to_base64(image_path)
    img_on_left = index % 2 == 0

    img_html = f'<img src="{img_b64}" alt="{title}" class="section-img">' if img_b64 else ""

    if img_on_left and img_html:
        layout = f"""
        <div class="section-inner layout-left">
            <div class="section-image">{img_html}</div>
            <div class="section-text">
                <div class="section-header">
                    <span class="section-icon">{icon}</span>
                    <h2>{title}</h2>
                </div>
                <div class="section-content">{content}</div>
            </div>
        </div>"""
    elif img_html:
        layout = f"""
        <div class="section-inner layout-right">
            <div class="section-text">
                <div class="section-header">
                    <span class="section-icon">{icon}</span>
                    <h2>{title}</h2>
                </div>
                <div class="section-content">{content}</div>
            </div>
            <div class="section-image">{img_html}</div>
        </div>"""
    else:
        layout = f"""
        <div class="section-inner">
            <div class="section-text full-width">
                <div class="section-header">
                    <span class="section-icon">{icon}</span>
                    <h2>{title}</h2>
                </div>
                <div class="section-content">{content}</div>
            </div>
        </div>"""

    return f'<section class="article-section">{layout}</section>'


def render_article(article_content: dict, images: dict) -> str:
    title = article_content["title"]
    intro = markdown_to_html(article_content["intro"])
    diagnosis = article_content.get("diagnosis")
    patient_name = article_content.get("patient_name")
    sections = article_content["sections"]
    today = format_date_en(date.today())

    hero_b64 = image_to_base64(images.get("hero"))
    hero_style = f'style="background-image: url({hero_b64}); background-size: cover; background-position: center;"' if hero_b64 else ""

    greeting = f"Prepared for <strong>{patient_name}</strong>" if patient_name else "Your personalized health guide"

    # Diagnosis card — hidden if no diagnosis
    if diagnosis and diagnosis.lower() not in ("none", "null", ""):
        diagnosis_card = f"""
        <div class="diagnosis-card">
            <div class="diagnosis-icon"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.9)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></div>
            <div>
                <div class="diagnosis-label">Your Diagnosis</div>
                <div class="diagnosis-value">{diagnosis}</div>
            </div>
        </div>"""
    else:
        diagnosis_card = ""

    section_keys = ["what", "mechanism", "treatment", "daily", "warning"]
    sections_html = ""
    for i, (section, key) in enumerate(zip(sections, section_keys)):
        sections_html += render_section(section, images.get(key), i)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            background: #F0F4F8;
            color: #1E2D3D;
            line-height: 1.75;
        }}

        /* ── Hero ── */
        .hero {{
            position: relative;
            min-height: 500px;
            display: flex;
            align-items: flex-end;
            background: linear-gradient(135deg, #0A2540 0%, #0D3B6E 60%, #1565A8 100%);
            overflow: hidden;
        }}

        .hero-bg {{
            position: absolute;
            inset: 0;
            background-size: cover;
            background-position: center;
            opacity: 0.2;
        }}

        .hero-accent {{
            position: absolute;
            top: 0; right: 0;
            width: 400px; height: 400px;
            background: radial-gradient(circle, rgba(0,180,216,0.3) 0%, transparent 70%);
            border-radius: 50%;
        }}

        .hero-content {{
            position: relative;
            z-index: 2;
            padding: 60px 80px;
            max-width: 820px;
        }}

        .hero-tag {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(0,180,216,0.2);
            border: 1px solid rgba(0,180,216,0.5);
            color: #00D4FF;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            padding: 6px 16px;
            border-radius: 20px;
            margin-bottom: 24px;
        }}

        .hero h1 {{
            font-size: 2.6rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.2;
            margin-bottom: 20px;
            letter-spacing: -0.5px;
        }}

        .hero-intro {{
            font-size: 1.05rem;
            color: rgba(255,255,255,0.8);
            max-width: 640px;
            margin-bottom: 32px;
            line-height: 1.7;
        }}

        .hero-meta {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.85rem;
            color: rgba(255,255,255,0.45);
        }}

        .hero-meta::before {{
            content: '';
            display: block;
            width: 32px;
            height: 2px;
            background: #00B4D8;
        }}

        /* ── Article body ── */
        .article-body {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 24px 40px 80px;
        }}

        /* ── Diagnosis card ── */
        .diagnosis-card {{
            background: linear-gradient(135deg, #0D3B6E, #1565A8);
            border-radius: 16px;
            padding: 36px 48px;
            margin: 32px 0;
            color: white;
            display: flex;
            align-items: center;
            gap: 28px;
            box-shadow: 0 8px 32px rgba(13,59,110,0.3);
        }}

        .diagnosis-icon {{ font-size: 3rem; flex-shrink: 0; }}

        .diagnosis-label {{
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 2.5px;
            text-transform: uppercase;
            color: #00D4FF;
            margin-bottom: 8px;
        }}

        .diagnosis-value {{
            font-size: 1.8rem;
            font-weight: 800;
            color: white;
        }}

        /* ── Sections ── */
        .article-section {{
            background: #ffffff;
            border-radius: 16px;
            margin: 24px 0;
            overflow: hidden;
            box-shadow: 0 2px 16px rgba(0,0,0,0.06);
            border: 1px solid rgba(0,0,0,0.04);
            transition: box-shadow 0.25s, transform 0.25s;
        }}

        .article-section:hover {{
            box-shadow: 0 8px 32px rgba(13,59,110,0.1);
            transform: translateY(-2px);
        }}

        .section-inner {{
            display: flex;
            align-items: stretch;
            min-height: 300px;
        }}

        .section-image {{
            flex: 0 0 42%;
            overflow: hidden;
            background: #EBF4FF;
        }}

        .section-img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}

        .section-text {{
            flex: 1;
            padding: 44px 52px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        .section-text.full-width {{
            padding: 44px 60px;
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 2px solid #EBF4FF;
        }}

        .section-icon {{ flex-shrink: 0; display: flex; align-items: center; }}

        .section-text h2 {{
            font-size: 1.4rem;
            font-weight: 700;
            color: #0D3B6E;
            letter-spacing: -0.3px;
        }}

        /* ── Section content typography ── */
        .section-content {{ font-size: 0.97rem; color: #3D5166; line-height: 1.85; }}
        .section-content p {{ margin-bottom: 14px; }}
        .section-content p:last-child {{ margin-bottom: 0; }}
        .section-content h3 {{
            font-size: 1rem;
            font-weight: 700;
            color: #0D3B6E;
            margin: 20px 0 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.85rem;
        }}
        .section-content ul {{
            margin: 10px 0 14px 0;
            padding-left: 20px;
        }}
        .section-content li {{
            margin-bottom: 8px;
            color: #3D5166;
        }}
        .section-content strong {{ color: #0D3B6E; font-weight: 600; }}

        /* ── Disclaimer ── */
        .disclaimer {{
            background: #EBF8FF;
            border-left: 4px solid #00B4D8;
            border-radius: 0 12px 12px 0;
            padding: 20px 28px;
            margin: 32px 0;
            font-size: 0.92rem;
            color: #0D3B6E;
        }}

        /* ── Footer ── */
        .article-footer {{
            text-align: center;
            padding: 36px 40px;
            color: #8FA3B1;
            font-size: 0.82rem;
            border-top: 1px solid #DDE8F0;
            margin-top: 40px;
        }}

        .footer-logo {{
            font-weight: 800;
            color: #0D3B6E;
            font-size: 1rem;
            letter-spacing: -0.3px;
            display: block;
            margin-bottom: 8px;
        }}

        /* ── Responsive ── */
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 1.7rem; }}
            .hero-content {{ padding: 40px 24px; }}
            .section-inner {{ flex-direction: column; }}
            .section-image {{ flex: 0 0 200px; }}
            .section-text {{ padding: 28px 24px; }}
            .section-text.full-width {{ padding: 28px 24px; }}
            .article-body {{ padding: 16px 16px 60px; }}
            .diagnosis-card {{ padding: 24px 28px; flex-direction: column; gap: 16px; }}
        }}
    </style>
</head>
<body>

    <div class="hero">
        <div class="hero-bg" {hero_style}></div>
        <div class="hero-accent"></div>
        <div class="hero-content">
            <div class="hero-tag">Charly · Personalized Health Guide</div>
            <h1>{title}</h1>
            <div class="hero-intro">{intro}</div>
            <div class="hero-meta">{greeting} · {today}</div>
        </div>
    </div>

    <div class="article-body">

        {diagnosis_card}

        {sections_html}

        <div class="disclaimer">
            <strong>Important:</strong> This article was generated from your medical report
            and reference sources (MedlinePlus / NIH). It is designed to help you understand your situation,
            not to replace your doctor's advice. Always consult a healthcare professional
            before modifying your treatment.
            <br><br>
            For any additional questions about your health, your coverage, or your care options,
            <strong>Alan Health Insurance</strong> is here to support you every step of the way.
            Reach out to your Alan advisor for personalized guidance tailored to your needs.
        </div>

    </div>

    <div class="article-footer">
        <span class="footer-logo">Charly</span>
        Sources: MedlinePlus (NIH) · Generated on {today}
    </div>

</body>
</html>"""

    return html


def save_article(article_content: dict, images: dict, filename: str = "article") -> str:
    html = render_article(article_content, images)
    filepath = OUTPUT_DIR / f"{filename}.html"
    with open(str(filepath), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Article saved: {filepath}")
    return str(filepath)
