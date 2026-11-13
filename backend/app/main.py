"""RepoMind API (Phase 1).

Two endpoints:
  POST /ingest -> clone a repo, chunk it, embed it, store it
  POST /ask    -> ask a question about an ingested repo
"""

from fastapi import FastAPI, HTTPException

from .ingest.ast_chunker import chunk_file
from .ingest.cloner import clone_repo, list_python_files, repo_name_from_url
from .ingest.vector_store import add_chunks, delete_collection
from .models import AskRequest, AskResponse, IngestRequest, IngestResponse, Source
from .rag.answer import answer_question
from .agents.graph import ask_with_agents
from fastapi.middleware.cors import CORSMiddleware
from .ingest.cloner import REPOS_DIR



app = FastAPI(title="RepoMind")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest):
    """Full ingest pipeline: clone -> chunk -> store."""
    name = repo_name_from_url(request.repo_url)
    try:
        folder = clone_repo(request.repo_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Clone failed: {e}")

    delete_collection(name)  # fresh ingest, no stale chunks
    all_chunks = []
    for py_file in list_python_files(folder):
        all_chunks.extend(chunk_file(py_file))

    stored = add_chunks(name, all_chunks)
    return IngestResponse(
        repo_name=name,
        files_ingested=len(list_python_files(folder)),
        chunks_stored=stored,
    )


@app.get("/repos")
def list_repos():
    if not REPOS_DIR.exists():
        return {"repos": []}
    return {"repos": sorted(p.name for p in REPOS_DIR.iterdir() if p.is_dir())}



@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Full Q&A pipeline: retrieve -> answer with citations."""
    result = answer_question(request.repo_name, request.question, top_k=request.top_k)
    return AskResponse(
        answer=result["answer"],
        sources=[Source(**s) for s in result["sources"]],
    )

@app.post("/ask-agents", response_model=AskResponse)
def ask_agents(request: AskRequest):
    """Agentic Q&A: Planner -> Explorer -> Analyst -> Critic,
    with citation checking and up to 3 exploration rounds."""
    result = ask_with_agents(request.repo_name, request.question)
    return AskResponse(
        answer=result["answer"],
        sources=[Source(**s) for s in result["sources"]],
    )
