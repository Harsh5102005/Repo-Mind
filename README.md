# RepoMind

**Ask questions about any GitHub repository — answers cite the exact file and line numbers.**

RepoMind is a RAG (Retrieval-Augmented Generation) system that lets you ingest a GitHub repository and ask natural language questions about its codebase. It uses a two-phase approach:

- **Quick Mode** — Fast, single-pass retrieval + answer
- **Agents Mode** — Multi-agent workflow (Planner → Explorer → Analyst → Critic) with citation verification and iterative exploration

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │     │   Backend API    │     │  Vector Store   │
│   (React/Vite)  │◄───►│   (FastAPI)      │◄───►│  (ChromaDB)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            ┌───────────────┐     ┌───────────────┐
            │  Ingestion    │     │    Q&A        │
            │  Pipeline     │     │  Pipeline     │
            └───────────────┘     └───────────────┘
```

### Backend Components

| Module | Purpose |
|--------|---------|
| `ingest/cloner.py` | Clone GitHub repos locally |
| `ingest/ast_chunker.py` | Parse Python files with tree-sitter, extract semantic chunks |
| `ingest/embedder.py` | Generate embeddings via sentence-transformers |
| `ingest/vector_store.py` | Store/retrieve chunks in ChromaDB |
| `rag/answer.py` | Quick Q&A: retrieve → answer with citations |
| `agents/graph.py` | Agentic Q&A: LangGraph multi-agent workflow |

### Frontend

- **React 19 + Vite** — Fast dev server and build
- **Oxlint** — Fast linting
- **CSS Modules** — Scoped styling

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r ../requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your GROQ_API_KEY (required for LLM calls)

# Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Open http://localhost:5173 — the frontend proxies API calls to http://localhost:8000.

---

## 📦 Usage

1. **Ingest a repository** — Paste a GitHub URL (e.g., `https://github.com/user/repo`) and click **Ingest**
2. **Select the repo** — Choose from the dropdown (auto-populated after ingest)
3. **Choose a mode**:
   - ⚡ **Quick** — Fast single-pass answer
   - 🤖 **Agents** — Multi-agent deep dive with citation verification
4. **Ask away** — "How does authentication work?", "Where is the retry logic?", "Explain the chunking strategy"

---

## 🔧 Configuration

### Backend Environment Variables (`.env`)

```env
# Required
GROQ_API_KEY=your_groq_api_key

# Optional
CHROMA_PERSIST_DIR=./chroma_db
REPOS_DIR=./repos
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Frontend

The API base URL is hardcoded to `http://127.0.0.1:8000` in `src/App.jsx`. For production, build with a custom env or use a reverse proxy.

---

## 📁 Project Structure

```
Repo-Analyzer/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph multi-agent workflow
│   │   ├── ingest/          # Ingestion pipeline
│   │   │   ├── cloner.py
│   │   │   ├── ast_chunker.py
│   │   │   ├── embedder.py
│   │   │   └── vector_store.py
│   │   ├── rag/             # Quick Q&A pipeline
│   │   │   └── answer.py
│   │   ├── main.py          # FastAPI entry point
│   │   ├── models.py        # Pydantic models
│   │   └── mcp_server.py    # MCP server (optional)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main UI component
│   │   ├── App.css          # Styles
│   │   └── main.jsx         # Entry point
│   ├── package.json
│   └── vite.config.js
├── .gitignore
├── README.md
└── requirements.txt         # Root requirements (for backend)
```

---

## 🛠️ Development

### Backend Commands

```bash
cd backend

# Run with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest tests/

# Lint (if configured)
ruff check .
```

### Frontend Commands

```bash
cd frontend

# Dev server
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

---

## 🧪 Testing Ingestion

```bash
# Via API
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/fastapi/fastapi"}'

# List ingested repos
curl http://localhost:8000/repos

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"repo_name": "fastapi", "question": "How does dependency injection work?"}'
```

---

## 📄 License

MIT License — feel free to use and modify.

---

## 🙏 Acknowledgments

- **FastAPI** — Modern Python web framework
- **ChromaDB** — Vector database
- **sentence-transformers** — Embeddings
- **LangChain/LangGraph** — LLM orchestration
- **Groq** — Fast LLM inference
- **tree-sitter** — Code parsing
- **React + Vite** — Frontend tooling