"""Embeddings for RepoMind (LangChain version).

Thin wrapper around HuggingFaceEmbeddings. One shared model instance,
so chunks and questions are always embedded in the same space.
"""

from typing import List

from langchain_huggingface import HuggingFaceEmbeddings

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384 numbers per vector
_embeddings = None


def get_embeddings():
    """Load the model once, reuse it for every call."""
    global _embeddings
    if _embeddings is None:
        print(f"Loading embedding model: {MODEL_NAME} ...")
        _embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
        print("Embedding model loaded.")
    return _embeddings


def embed_texts(texts: List[str]) -> List[List[float]]:
    """List of strings -> list of vectors (same order)."""
    if not texts:
        return []
    return get_embeddings().embed_documents(texts)


def embed_query(query: str) -> List[float]:
    """One question -> one vector (same model as the chunks)."""
    return get_embeddings().embed_query(query)
