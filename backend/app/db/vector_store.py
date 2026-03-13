"""ChromaDB client for vector storage."""

import logging
from pathlib import Path

import chromadb

from app.config import config

logger = logging.getLogger(__name__)

# Ensure directory exists
Path(config.database.chroma_persist_dir).mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=config.database.chroma_persist_dir)


def get_website_collection():
    """Get or create the website_content collection."""
    return client.get_or_create_collection(
        name="website_content",
        metadata={"hnsw:space": "cosine"},
    )


def get_knowledge_collection():
    """Get or create the knowledge_base collection."""
    return client.get_or_create_collection(
        name="knowledge_base",
        metadata={"hnsw:space": "cosine"},
    )


def store_website_content(conversation_id: int, pages: list[dict]) -> int:
    """Store crawled website pages in ChromaDB.

    Returns number of documents stored.
    """
    collection = get_website_collection()
    count = 0

    for i, page in enumerate(pages):
        text = page.get("text", "")
        if not text:
            continue

        # Split long texts into chunks
        chunks = _split_text(text, max_length=1000)
        for j, chunk in enumerate(chunks):
            doc_id = f"conv_{conversation_id}_page_{i}_chunk_{j}"
            collection.upsert(
                ids=[doc_id],
                documents=[chunk],
                metadatas=[{
                    "conversation_id": str(conversation_id),
                    "url": page.get("url", ""),
                    "title": page.get("title", ""),
                    "chunk_index": j,
                }],
            )
            count += 1

    return count


def query_website_content(conversation_id: int, query: str, n_results: int = 5) -> list[dict]:
    """Query website content for a specific conversation."""
    collection = get_website_collection()
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"conversation_id": str(conversation_id)},
    )

    docs = []
    if results and results.get("documents"):
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            docs.append({"content": doc, "metadata": meta})

    return docs


def _split_text(text: str, max_length: int = 1000) -> list[str]:
    """Split text into chunks at sentence boundaries."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_length and current:
            chunks.append(current.strip())
            current = line
        else:
            current += "\n" + line if current else line

    if current.strip():
        chunks.append(current.strip())

    return chunks
