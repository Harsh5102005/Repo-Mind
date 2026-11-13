"""Tools for the RepoMind agent team (Phase 2).

The Explorer agent searches the codebase through this tool. A new
tool is built per run, bound to one repo, so the LLM only ever
passes a query string — it can never search the wrong repo.
"""

import os
import sys

from langchain_core.tools import tool

try:
    from ..rag.retriever import get_retriever
except ImportError:
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(_here, "..", "rag"))
    sys.path.insert(0, os.path.join(_here, "..", "ingest"))
    from retriever import get_retriever


def make_search_tool(repo_name: str, top_k: int = 5):
    """Build a code-search tool bound to one ingested repo."""

    @tool
    def search_code(query: str) -> str:
        """Search the codebase for code relevant to a question.
        Returns matching functions/classes with file, symbol and line numbers."""
        retriever = get_retriever(repo_name, top_k=top_k)
        docs = retriever.invoke(query)
        if not docs:
            return "No matching code found."
        lines = []
        for i, doc in enumerate(docs, start=1):
            meta = doc.metadata
            header = (
                f"[Source {i}] {meta.get('file_path')} "
                f"({meta.get('symbol_name')}, lines "
                f"{meta.get('start_line')}-{meta.get('end_line')})"
            )
            lines.append(f"{header}\n{doc.page_content}")
        return "\n\n".join(lines)

    return search_code


if __name__ == "__main__":
    # Test against the demo collection from the retriever test.
    search = make_search_tool("demo-test")
    print(search.invoke({"query": "how does a user sign in?"}))
