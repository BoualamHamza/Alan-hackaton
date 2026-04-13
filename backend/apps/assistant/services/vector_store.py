"""
Builds and queries the ChromaDB vector store from MedlinePlus topics.
- Chunks each topic summary into smaller pieces
- Embeds them via Mistral Embed API
- Stores them in a local ChromaDB collection
"""

import json
import time
from pathlib import Path

import chromadb
from mistralai import Mistral

from ..core.config import settings

# Path to the ChromaDB local storage
REPO_ROOT = Path(__file__).resolve().parents[4]
ASSISTANT_DATA_DIR = REPO_ROOT / "asistant" / "data"
CHROMA_PATH = str(ASSISTANT_DATA_DIR / "chroma")
TOPICS_PATH = str(ASSISTANT_DATA_DIR / "medlineplus" / "topics.json")

COLLECTION_NAME = "medlineplus"
CHUNK_SIZE = 512        # max characters per chunk
CHUNK_OVERLAP = 64      # overlap between chunks to preserve context
BATCH_SIZE = 50         # number of chunks per embedding API call


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Splits a long text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


def build_vector_store() -> None:
    """
    Reads topics.json, chunks summaries, embeds them via Mistral,
    and stores everything in ChromaDB.
    """
    print("Loading topics...")
    with open(TOPICS_PATH, "r", encoding="utf-8") as f:
        topics = json.load(f)

    client = Mistral(api_key=settings.mistral_api_key)
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

    all_chunks = []
    all_ids = []
    all_metadata = []

    print("Chunking topics...")
    for topic in topics:
        summary = topic.get("summary", "")
        if not summary:
            continue

        chunks = chunk_text(summary)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{topic['id']}_{i}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadata.append({
                "topic_id": topic["id"],
                "title": topic["title"],
                "url": topic.get("url", ""),
                "chunk_index": i,
            })

    print(f"Total chunks to embed: {len(all_chunks)}")

    # Find already-indexed IDs to resume from where we left off
    existing_ids = set(collection.get(include=[])["ids"])
    print(f"Already indexed: {len(existing_ids)} chunks. Resuming...")

    # Embed and store in batches
    for batch_start in range(0, len(all_chunks), BATCH_SIZE):
        batch_chunks = all_chunks[batch_start: batch_start + BATCH_SIZE]
        batch_ids = all_ids[batch_start: batch_start + BATCH_SIZE]
        batch_meta = all_metadata[batch_start: batch_start + BATCH_SIZE]

        # Skip chunks already indexed
        to_process = [
            (chunk, id_, meta)
            for chunk, id_, meta in zip(batch_chunks, batch_ids, batch_meta)
            if id_ not in existing_ids
        ]
        if not to_process:
            continue

        batch_chunks, batch_ids, batch_meta = zip(*to_process)

        # Retry with exponential backoff on rate limit
        for attempt in range(5):
            try:
                response = client.embeddings.create(
                    model="mistral-embed",
                    inputs=list(batch_chunks),
                )
                break
            except Exception as e:
                if "429" in str(e) or "rate_limited" in str(e):
                    wait = 2 ** attempt * 5
                    print(f"  Rate limit hit, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raise

        embeddings = [item.embedding for item in response.data]

        collection.add(
            ids=list(batch_ids),
            embeddings=embeddings,
            documents=list(batch_chunks),
            metadatas=list(batch_meta),
        )

        progress = min(batch_start + BATCH_SIZE, len(all_chunks))
        print(f"  Embedded {progress}/{len(all_chunks)} chunks...")

        time.sleep(0.5)

    print(f"Vector store built successfully — {len(all_chunks)} chunks stored in ChromaDB.")


def retrieve(query: str, k: int = 5) -> list[dict]:
    """
    Embeds the query and retrieves the k most relevant chunks from ChromaDB.
    Returns a list of dicts with text content and metadata.
    """
    client = Mistral(api_key=settings.mistral_api_key)
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_collection(COLLECTION_NAME)

    response = client.embeddings.create(
        model="mistral-embed",
        inputs=[query],
    )
    query_embedding = response.data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
    )

    retrieved = []
    for i in range(len(results["documents"][0])):
        retrieved.append({
            "text": results["documents"][0][i],
            "title": results["metadatas"][0][i]["title"],
            "url": results["metadatas"][0][i]["url"],
        })

    return retrieved


if __name__ == "__main__":
    build_vector_store()
