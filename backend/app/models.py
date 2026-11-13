"""Request/response shapes for the RepoMind API."""

from typing import List, Optional

from pydantic import BaseModel


class IngestRequest(BaseModel):
    repo_url: str  # e.g. https://github.com/user/repo


class IngestResponse(BaseModel):
    repo_name: str
    files_ingested: int
    chunks_stored: int


class AskRequest(BaseModel):
    repo_name: str  # must match a repo you already ingested
    question: str
    top_k: Optional[int] = 5


class Source(BaseModel):
    file_path: str
    symbol_name: str
    start_line: int
    end_line: int


class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
