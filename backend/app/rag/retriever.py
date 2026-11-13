"""Retriever for RepoMind (LangChain version).

This is the .as_retriever() idea, wired to our per-repo Chroma store:
question string in -> best Documents out.
"""

try:
    from ..ingest.vector_store import get_vectorstore, add_chunks, delete_collection
    from ..ingest.ast_chunker import Chunk
except ImportError:
    import os
    import sys
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _here)  # rag/ folder
    sys.path.insert(0, os.path.join(_here, "..", "ingest"))  # ingest/ folder
    from vector_store import get_vectorstore, add_chunks, delete_collection
    from ast_chunker import Chunk



def get_retriever(repo_name: str, top_k: int = 5):
    """Return a LangChain Retriever for one repo."""
    return get_vectorstore(repo_name).as_retriever(
        search_kwargs={"k": top_k}
    )


def retrieve(repo_name: str, question: str, top_k: int = 5):
    """Question string in -> best Documents out."""
    return get_retriever(repo_name, top_k).invoke(question)


if __name__ == "__main__":
    # Test: 3 demo chunks, one question, login_user must win.
    delete_collection("demo-test")

    demo = [
        Chunk(
            text="def login_user(email, password):\n    return verify(email, password)",
            file_path="auth.py", symbol_type="function",
            symbol_name="login_user", start_line=1, end_line=2,
        ),
        Chunk(
            text="def play_video(path):\n    return open_player(path)",
            file_path="player.py", symbol_type="function",
            symbol_name="play_video", start_line=1, end_line=2,
        ),
        Chunk(
            text="def fetch_profile(user_id):\n    return db.get(user_id)",
            file_path="users.py", symbol_type="function",
            symbol_name="fetch_profile", start_line=1, end_line=2,
        ),
    ]
    add_chunks("demo-test", demo)

    print("\nQuestion: how does a user sign in?\n")
    for doc in retrieve("demo-test", "how does a user sign in?", top_k=3):
        m = doc.metadata
        print(f"  {m['symbol_name']} ({m['file_path']}:{m['start_line']}-{m['end_line']})")
