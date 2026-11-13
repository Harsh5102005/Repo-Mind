"""Vector store for RepoMind (LangChain version).

One Chroma collection per repo. Chunks become LangChain Documents,
so citations live in each Document's metadata.
"""

import hashlib
import re
from pathlib import Path
from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document

try:
    from .ast_chunker import Chunk
    from .embedder import get_embeddings
except ImportError:
    from ast_chunker import Chunk
    from embedder import get_embeddings


DB_DIR = Path(__file__).resolve().parents[3] / "data" / "chroma_db"


def _sanitize_collection_name(name: str) -> str:
    """ChromaDB names: 3-63 chars, letters/digits/./_/- only."""
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", name.lower()).strip("-._")
    if len(slug) < 3:
        slug = (slug + "---")[:3]
    return slug[:63]


def get_vectorstore(repo_name: str) -> Chroma:
    """Get the repo's Chroma store, creating it if needed."""
    return Chroma(
        collection_name=_sanitize_collection_name(repo_name),
        persist_directory=str(DB_DIR),
        embedding_function=get_embeddings(),
        collection_metadata={"hnsw:space": "cosine"},
    )


def _chunk_id(chunk: Chunk) -> str:
    """Stable id per chunk: re-ingesting overwrites instead of duplicating."""
    raw = f"{chunk.file_path}:{chunk.symbol_name}:{chunk.start_line}-{chunk.end_line}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def chunk_to_document(chunk: Chunk) -> Document:
    """Chunk -> Document. The citation data becomes metadata."""
    return Document(
        page_content=chunk.text,
        metadata={
            "file_path": chunk.file_path,
            "symbol_type": chunk.symbol_type,
            "symbol_name": chunk.symbol_name,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
        },
    )


def add_chunks(repo_name: str, chunks: List[Chunk]) -> int:
    """Store chunks. Returns how many were stored."""
    if not chunks:
        return 0
    vs = get_vectorstore(repo_name)
    vs.add_documents(
        [chunk_to_document(c) for c in chunks],
        ids=[_chunk_id(c) for c in chunks],
    )
    return len(chunks)


def search(repo_name: str, query: str, top_k: int = 5):
    """Question string in -> ranked (Document, similarity) pairs out."""
    vs = get_vectorstore(repo_name)
    results = vs.similarity_search_with_score(query, k=top_k)
    # Cosine space: distance -> similarity (higher = closer)
    return [(doc, round(1 - score, 3)) for doc, score in results]


def delete_collection(repo_name: str):
    """Delete a repo's collection (clean slate for re-ingesting)."""
    import chromadb

    client = chromadb.PersistentClient(path=str(DB_DIR))
    try:
        client.delete_collection(name=_sanitize_collection_name(repo_name))
    except Exception:
        pass  # did not exist; nothing to delete
