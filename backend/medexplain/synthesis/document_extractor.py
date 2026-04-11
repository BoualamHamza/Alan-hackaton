"""
Extract text content from uploaded medical documents.
Supports PDF (pypdf), images (Mistral vision), and placeholders for docx.
"""
from __future__ import annotations

import base64
import io

from mistralai.client import Mistral
from config import settings


async def extract_documents(file_tuples: list[tuple[str, bytes, str]]) -> str:
    """
    Extract text from a list of uploaded files.

    Args:
        file_tuples: list of (filename, file_bytes, content_type)

    Returns:
        Merged text string with per-document headers.
    """
    if not file_tuples:
        return ""

    parts: list[str] = []
    for filename, file_bytes, content_type in file_tuples:
        parts.append(f"--- Document: {filename} ---")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext == "pdf":
            text = _extract_pdf(file_bytes)
            parts.append(text if text.strip() else "[PDF contained no extractable text]")

        elif ext in ("jpg", "jpeg", "png"):
            text = await _extract_image(file_bytes, content_type)
            parts.append(text)

        elif ext in ("docx", "doc"):
            parts.append("[DOCX/DOC text extraction not implemented — please upload as PDF]")

        else:
            parts.append(f"[Unsupported file type: .{ext}]")

    return "\n\n".join(parts)


def _extract_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    except Exception as e:
        return f"[PDF extraction error: {e}]"


async def _extract_image(file_bytes: bytes, content_type: str) -> str:
    """Use Mistral vision to extract text from a medical image."""
    try:
        mime = content_type if content_type.startswith("image/") else "image/jpeg"
        b64 = base64.standard_b64encode(file_bytes).decode()
        data_url = f"data:{mime};base64,{b64}"

        client = Mistral(api_key=settings.mistral_api_key)
        response = client.chat.complete(
            model="pixtral-12b-2409",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                        {
                            "type": "text",
                            "text": (
                                "This is a medical document image. "
                                "Please extract all visible text and describe all medical "
                                "information, values, diagnoses, medications, and findings "
                                "present in this image. Be thorough and precise."
                            ),
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content or "[No text extracted from image]"
    except Exception as e:
        return f"[Image extraction error: {e}]"
