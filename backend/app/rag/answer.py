"""Answer stage for RepoMind (LangChain version).

Retrieved Documents + question -> LLM answer with citations.
Uses Groq (fast, and you already use it). Key: GROQ_API_KEY in .env.
"""

import os
from typing import Dict, List

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.documents import Document

try:
    from .retriever import retrieve
    from ..ingest.vector_store import add_chunks, delete_collection
    from ..ingest.ast_chunker import Chunk
except ImportError:
    import os
    import sys
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _here)
    sys.path.insert(0, os.path.join(_here, "..", "ingest"))
    from retriever import retrieve
    from vector_store import add_chunks, delete_collection
    from ast_chunker import Chunk



load_dotenv()  # reads GROQ_API_KEY from .env

_llm = None


def _get_llm() -> ChatGroq:
    """Load the chat model once, reuse it for every question."""
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0,  # 0 = factual, no creative guessing
        )
    return _llm


def format_context(docs: List[Document]) -> str:
    """Number the chunks and attach their citation data, so the
    LLM can quote file + lines for every claim it makes."""
    parts = []
    for i, doc in enumerate(docs, start=1):
        m = doc.metadata
        parts.append(
            f"[Source {i}] {m['file_path']} | {m['symbol_type']} "
            f"{m['symbol_name']} | lines {m['start_line']}-{m['end_line']}\n"
            f"{doc.page_content}"
        )
    return "\n\n".join(parts)


def build_prompt(question: str, docs: List[Document]) -> str:
    """Strict prompt: only the given code is evidence. No guessing."""
    return (
        "You are RepoMind, a code assistant. Answer the question using "
        "ONLY the code sources below.\n\n"
        "Rules:\n"
        "- Cite every claim as [Source N] with its file and lines.\n"
        "- If the code does not contain the answer, say "
        "'Not found in the code.' Do not guess.\n"
        "- Keep the answer short and focused on the question.\n\n"
        f"Code sources:\n{format_context(docs)}\n\n"
        f"Question: {question}\n"
        "Answer:"
    )


def answer_question(repo_name: str, question: str, top_k: int = 5) -> Dict:
    """Full Q&A step: retrieve -> prompt -> LLM -> answer + sources."""
    docs = retrieve(repo_name, question, top_k=top_k)
    if not docs:
        return {
            "answer": "Not found in the code.",
            "sources": [],
        }
    response = _get_llm().invoke(build_prompt(question, docs))
    return {
        "answer": response.content,
        "sources": [
            {
                "file_path": d.metadata["file_path"],
                "symbol_name": d.metadata["symbol_name"],
                "start_line": d.metadata["start_line"],
                "end_line": d.metadata["end_line"],
            }
            for d in docs
        ],
    }


if __name__ == "__main__":
    # Self-contained test: ingest 3 demo chunks, then ask about login.
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

    result = answer_question("demo-test", "How does a user sign in?")
    print("\nAnswer:", result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  {s['file_path']} | {s['symbol_name']} | "
              f"lines {s['start_line']}-{s['end_line']}")
