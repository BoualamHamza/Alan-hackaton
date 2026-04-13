"""
GET /articles?query=... — retrieve MedlinePlus articles relevant to a case.
Uses the existing ChromaDB vector store; deduplicates by topic title.
"""

import re
from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..services.vector_store import retrieve


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]*>?", " ", text)   # complete and truncated tags
    text = re.sub(r"\s+", " ", text)
    return text.strip()

router = APIRouter(tags=["Articles"])


class Article(BaseModel):
    title: str
    url: str
    excerpt: str
    source: str = "MedlinePlus"


@router.get("/articles", response_model=list[Article])
def get_articles(
    query: str = Query(..., description="Search query built from case specialty + symptoms"),
    k: int = Query(default=5, le=10),
):
    """
    Retrieve the top-k most relevant MedlinePlus articles for a case query.
    Deduplicates by topic title so each article appears only once.
    """
    # Fetch more chunks than needed to allow for deduplication
    chunks = retrieve(query, k=k * 4)

    # Deduplicate: keep the longest chunk per unique (title, url) pair
    seen: dict[str, Article] = {}
    for chunk in chunks:
        title = chunk["title"]
        clean = strip_html(chunk["text"])
        if title not in seen or len(clean) > len(seen[title].excerpt):
            seen[title] = Article(
                title=title,
                url=chunk["url"],
                excerpt=clean,
            )

    return list(seen.values())[:k]
