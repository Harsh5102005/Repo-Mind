"""Shared state for the RepoMind agent team (Phase 2).

Every agent reads from and writes to this one object as it moves
through the graph. Fields with Annotated[..., operator.add] accumulate
across steps instead of being overwritten.
"""

import operator
from typing import Annotated, List

from langchain_core.documents import Document
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # Inputs (set once at the start, never changed)
    question: str
    repo_name: str

    # Planner output: the search steps to run
    plan: List[str]

    # Explorer output: evidence gathered so far. The operator.add
    # annotation means each Explorer visit APPENDS new chunks to
    # this list instead of replacing the old ones.
    evidence: Annotated[List[Document], operator.add]

    # Analyst output: the draft answer
    draft: str

    # Critic output: what is wrong (empty if approved)
    critique: str

    # Critic verdict + loop guard
    approved: bool
    iterations: int
