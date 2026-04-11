"""
Step 4 — Medical image search via Pexels API.
For each article section, finds a high-quality relevant photo
and returns it as a local file path for embedding in the HTML article.
"""

import os
import httpx
from pathlib import Path

ENV_PATH = os.path.join(os.path.dirname(__file__), "../../.env")

OUTPUT_DIR = Path(__file__).parent.parent / "generated_images"
OUTPUT_DIR.mkdir(exist_ok=True)

PEXELS_API_URL = "https://api.pexels.com/v1/search"

# Curated search queries per section — optimized for medical/health photos
SECTION_QUERIES = {
    "hero":      "{diagnosis} health care patient",
    "what":      "{diagnosis} human body anatomy",
    "mechanism": "{diagnosis} medical science biology",
    "treatment": "{diagnosis} treatment medicine recovery",
    "daily":     "healthy lifestyle wellness daily routine",
    "warning":   "doctor patient consultation hospital",
}


def _get_api_key() -> str:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        raise ValueError("PEXELS_API_KEY not set.")
    return key


def search_image(query: str, section: str) -> str | None:
    """
    Searches Pexels for a relevant photo and downloads it.
    Returns local file path or None if not found.
    """
    api_key = _get_api_key()

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                PEXELS_API_URL,
                headers={"Authorization": api_key},
                params={
                    "query": query,
                    "per_page": 5,
                    "orientation": "landscape",
                    "size": "large",
                },
            )
            response.raise_for_status()
            data = response.json()

            photos = data.get("photos", [])
            if not photos:
                # Fallback to a more generic query
                fallback_queries = {
                    "hero": "healthcare patient doctor",
                    "what": "human body medical",
                    "mechanism": "medical science research",
                    "treatment": "medicine recovery health",
                    "daily": "healthy lifestyle wellness",
                    "warning": "doctor consultation hospital",
                }
                fallback = fallback_queries.get(section, "healthcare medical")
                response = client.get(
                    PEXELS_API_URL,
                    headers={"Authorization": api_key},
                    params={"query": fallback, "per_page": 3, "orientation": "landscape"},
                )
                response.raise_for_status()
                data = response.json()
                photos = data.get("photos", [])

            if not photos:
                return None

            # Pick the best photo (first result, landscape, high res)
            photo = photos[0]
            img_url = photo["src"]["large2x"]  # high quality

            # Download the image
            img_response = client.get(img_url, timeout=30.0)
            img_response.raise_for_status()

            filepath = OUTPUT_DIR / f"article_{section}.jpg"
            with open(str(filepath), "wb") as f:
                f.write(img_response.content)

            print(f"  Image found: '{photo['photographer']}' — {photo['url']}")
            return str(filepath)

    except Exception as e:
        print(f"  Pexels search failed for '{query}': {e}")
        return None


def generate_all_images(image_keywords: dict) -> dict:
    """
    Finds one Pexels photo per article section.
    image_keywords: {"hero": "nasopharyngitis medical", "what": "...", ...}
    Returns dict mapping section → local file path (or None if failed).
    """
    images = {}
    for section, keyword in image_keywords.items():
        query = SECTION_QUERIES.get(section, "{diagnosis} health").replace(
            "{diagnosis}", keyword.split()[0]
        )
        print(f"Searching Pexels for section '{section}': {query}")
        path = search_image(query, section)
        images[section] = path
        print(f"  → {'Saved' if path else 'Failed'}")

    return images
