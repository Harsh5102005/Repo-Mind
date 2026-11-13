"""The RepoMind agent graph (Phase 2).

planner -> explorer -> analyst -> critic -> (approved? END : explorer)
The critic loop is capped at MAX_ITERATIONS so a question always
gets an answer instead of looping forever.
"""

import os
import sys

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

load_dotenv()

try:
    from .state import AgentState
    from ..rag.answer import build_prompt, format_context
    from ..rag.retriever import get_retriever
except ImportError:
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _here)
    sys.path.insert(0, os.path.join(_here, "..", "rag"))
    sys.path.insert(0, os.path.join(_here, "..", "ingest"))
    from state import AgentState
    from answer import build_prompt, format_context
    from retriever import get_retriever

MAX_ITERATIONS = 3
_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
    return _llm


def planner(state: AgentState):
    """Break the question into 2-4 short search queries."""
    prompt = (
        "Break this question about a codebase into 2-4 short search "
        "queries, one per line, no numbering or bullet points.\n"
        f"Question: {state['question']}"
    )
    out = _get_llm().invoke(prompt).content
    plan = [line.strip().lstrip("0123456789.-) ").strip()
            for line in out.splitlines() if line.strip()]
    return {"plan": plan[:4]}


def explorer(state: AgentState):
    """Run each planned search; accumulate unique evidence."""
    retriever = get_retriever(state["repo_name"], top_k=5)
    queries = state.get("plan") or [state["question"]]
    docs = []
    for query in queries:
        docs.extend(retriever.invoke(query))
    seen, unique = set(), []
    for doc in docs:
        key = (doc.metadata.get("file_path"),
               doc.metadata.get("symbol_name"),
               doc.metadata.get("start_line"))
        if key not in seen:
            seen.add(key)
            unique.append(doc)
    return {"evidence": unique, "iterations": state.get("iterations", 0) + 1}


def analyst(state: AgentState):
    """Draft the answer from the gathered evidence only."""
    prompt = build_prompt(state["question"], state["evidence"])
    draft = _get_llm().invoke(prompt).content
    return {"draft": draft}



def critic(state: AgentState):
    """Approve only if every claim cites the evidence.
    Otherwise name exactly what is missing."""
    context = format_context(state["evidence"])
    prompt = (
        "You are a strict reviewer. Check the draft answer against "
        "the code evidence below.\n"
        "If every claim is supported by a cited [Source N], reply with "
        "exactly: APPROVED\n"
        "Otherwise reply with: NEEDS MORE: <what evidence is missing>\n\n"
        f"Question: {state['question']}\n\n"
        f"Evidence:\n{context}\n\n"
        f"Draft:\n{state['draft']}"
    )
    verdict = _get_llm().invoke(prompt).content.strip()
    if verdict.startswith("APPROVED"):
        return {"approved": True, "critique": ""}
    return {"approved": False, "critique": verdict}


def route_after_critic(state: AgentState):
    """END when approved or out of rounds, else explore again."""
    if state.get("approved") or state.get("iterations", 0) >= MAX_ITERATIONS:
        return "done"
    return "retry"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("planner", planner)
    graph.add_node("explorer", explorer)
    graph.add_node("analyst", analyst)
    graph.add_node("critic", critic)
    graph.set_entry_point("planner")
    graph.add_edge("planner", "explorer")
    graph.add_edge("explorer", "analyst")
    graph.add_edge("analyst", "critic")
    graph.add_conditional_edges(
        "critic", route_after_critic, {"done": END, "retry": "explorer"}
    )
    return graph.compile()


def ask_with_agents(repo_name: str, question: str):
    """Run the full agent team; return answer + citation sources."""
    graph = build_graph()
    result = graph.invoke({
        "question": question,
        "repo_name": repo_name,
        "plan": [],
        "evidence": [],
        "draft": "",
        "critique": "",
        "approved": False,
        "iterations": 0,
    })
    sources = [{
        "file_path": d.metadata.get("file_path"),
        "symbol_name": d.metadata.get("symbol_name"),
        "start_line": d.metadata.get("start_line"),
        "end_line": d.metadata.get("end_line"),
    } for d in result["evidence"]]
    return {"answer": result["draft"], "sources": sources}


if __name__ == "__main__":
    # Test against the demo collection from the retriever test.
    out = ask_with_agents("demo-test", "How does a user sign in?")
    print(out["answer"])
    print("\nSources:")
    for s in out["sources"]:
        print(f"  {s['file_path']} ({s['symbol_name']}, lines {s['start_line']}-{s['end_line']})")
