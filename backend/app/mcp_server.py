"""RepoMind MCP server (Phase 2b).

Exposes RepoMind's pipeline as MCP tools so any MCP-compatible
client (Claude Desktop, an agent, the MCP Inspector) can:
  - ingest a repo (clone -> chunk -> embed -> store)
  - search an ingested repo's code
  - list the Python files in an ingested repo
"""

import os
import sys
from pathlib import Path

from mcp.server.mcpserver import MCPServer


try:
    from .ingest.ast_chunker import chunk_file
    from .ingest.cloner import REPOS_DIR, clone_repo, list_python_files, repo_name_from_url

    from .ingest.vector_store import add_chunks, delete_collection
    from .rag.retriever import get_retriever
except ImportError:
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(_here, "ingest"))
    sys.path.insert(0, os.path.join(_here, "rag"))
    from ast_chunker import chunk_file
    from cloner import REPOS_DIR, clone_repo, list_python_files, repo_name_from_url

    from vector_store import add_chunks, delete_collection
    from retriever import get_retriever

mcp = MCPServer("RepoMind")



@mcp.tool()
def ingest_repo(repo_url: str) -> str:
    """Clone a GitHub repo, chunk its Python files, and store them
    for searching. Returns a summary of what was ingested."""
    name = repo_name_from_url(repo_url)
    folder = clone_repo(repo_url)
    delete_collection(name)
    all_chunks = []
    for py_file in list_python_files(folder):
        all_chunks.extend(chunk_file(py_file))
    if not all_chunks:
        return (f"Cloned '{name}', but found no Python functions/classes to "
            f"index — nothing was stored.")

    stored = add_chunks(name, all_chunks)
    return (f"Ingested '{name}': {len(list_python_files(folder))} Python "
            f"files, {stored} chunks stored. You can now search it.")


@mcp.tool()
def search_code(repo_name: str, query: str, top_k: int = 5) -> str:
    """Search an ingested repo's code for functions/classes relevant
    to a question. Returns matching chunks with file, symbol and
    line numbers for citations."""
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


@mcp.tool()
def list_files(repo_name: str) -> str:
    """List the Python files in an ingested repo."""
    folder = REPOS_DIR / repo_name
    if not folder.exists():
        return f"Repo '{repo_name}' is not ingested yet. Call ingest_repo first."
    files = list_python_files(folder)
    return "\n".join(str(f.relative_to(folder)) for f in files)


if __name__ == "__main__":
    mcp.run()
