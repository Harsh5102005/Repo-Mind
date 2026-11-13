import { useEffect, useRef, useState } from "react";
import "./App.css";

// Use Vite proxy in dev, direct URL in production
const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [repos, setRepos] = useState([]);
  const [repo, setRepo] = useState("");
  const [mode, setMode] = useState("quick"); // "quick" -> /ask, "agents" -> /ask-agents
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [ingestMsg, setIngestMsg] = useState("");
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, busy]);

  const loadRepos = async () => {
    try {
      const r = await fetch(`${API}/repos`);
      const data = await r.json();
      setRepos(data.repos || []);
      if (data.repos?.length) setRepo((cur) => cur || data.repos[0]);
    } catch {
      setRepos([]);
    }
  };

  useEffect(() => { loadRepos(); }, []);

  const ingest = async () => {
    if (!repoUrl.trim() || busy) return;
    setBusy(true);
    setIngestMsg("Cloning and indexing… this may take a moment");
    try {
      const r = await fetch(`${API}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl.trim() }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Ingest failed");
      setIngestMsg(`Ingested ${data.files_ingested} files · ${data.chunks_stored} chunks stored`);
      setRepoUrl("");
      await loadRepos();
      setRepo(data.repo_name);
    } catch (e) {
      setIngestMsg(`Error: ${e.message}`);
    }
    setBusy(false);
  };

  const ask = async () => {
    if (!question.trim() || !repo || busy) return;
    const q = question.trim();
    setQuestion("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setBusy(true);
    try {
      const endpoint = mode === "agents" ? "/ask-agents" : "/ask";
      const r = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_name: repo, question: q }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Request failed");
      setMessages((m) => [...m, {
        role: "assistant", text: data.answer, sources: data.sources || [],
      }]);
    } catch (e) {
      setMessages((m) => [...m, {
        role: "assistant", text: `Error: ${e.message}`, sources: [],
      }]);
    }
    setBusy(false);
  };

  return (
    <div className="app">
      {/* ── Header ── */}
      <header>
        <div className="logo-row">
          <div className="logo-icon">🧠</div>
          <h1>RepoMind</h1>
        </div>
        <p className="subtitle">
          Ask questions about any GitHub repo — answers cite the exact file &amp; lines.
        </p>
      </header>

      {/* ── Ingest Section ── */}
      <section className="ingest glass-card">
        <div className="ingest-label">
          <span className="label-dot" />
          <span>Add a Repository</span>
        </div>
        <div className="ingest-row">
          <input
            id="repo-url-input"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ingest()}
            placeholder="https://github.com/user/repo"
          />
          <button
            id="ingest-btn"
            className="btn btn-primary"
            onClick={ingest}
            disabled={busy || !repoUrl.trim()}
          >
            <span className="btn-icon">⬇</span>
            Ingest
          </button>
        </div>
        {ingestMsg && (
          <div className="status">
            <span className="status-icon">{ingestMsg.startsWith("Error") ? "⚠" : busy ? "⏳" : "✓"}</span>
            {ingestMsg}
          </div>
        )}
      </section>

      {/* ── Controls ── */}
      <section className="controls glass-card">
        <div className="controls-inner">
          <div className="select-wrapper">
            <select
              id="repo-select"
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
            >
              <option value="" disabled>Select a repository…</option>
              {repos.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>

          <div className="mode-toggle">
            <button
              id="mode-quick"
              className={`mode-btn ${mode === "quick" ? "active" : ""}`}
              onClick={() => setMode("quick")}
            >
              <span className="mode-icon">⚡</span>
              <span className="mode-label">Quick</span>
            </button>
            <button
              id="mode-agents"
              className={`mode-btn ${mode === "agents" ? "active" : ""}`}
              onClick={() => setMode("agents")}
            >
              <span className="mode-icon">🤖</span>
              <span className="mode-label">Agents</span>
            </button>
          </div>
        </div>
      </section>

      {/* ── Chat Area ── */}
      <section className="chat">
        {messages.length === 0 && !busy && (
          <div className="empty-state">
            <div className="empty-icon">💬</div>
            <div className="empty-title">Start a Conversation</div>
            <p className="empty-desc">
              Ingest a GitHub repo, then ask anything — architecture, logic, bugs, or how a specific function works.
            </p>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <div className="msg-label">{m.role === "user" ? "You" : "RepoMind"}</div>
            <div className="msg-bubble">{m.text}</div>
            {m.sources?.length > 0 && (
              <div className="sources">
                {m.sources.map((s, j) => (
                  <div key={j} className="source">
                    <span className="file">📄 {s.file_path}</span>
                    <span className="sym">{s.symbol_name} · lines {s.start_line}–{s.end_line}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {busy && (
          <div className="msg assistant">
            <div className="msg-label">RepoMind</div>
            <div className="msg-bubble thinking">Thinking…</div>
          </div>
        )}
        <div ref={chatEndRef} />
      </section>

      {/* ── Ask Bar ── */}
      <div className="askbar-wrapper">
        <div className="askbar">
          <input
            id="ask-input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask()}
            placeholder={repo ? `Ask about ${repo}…` : "Ingest a repo first…"}
            disabled={!repo}
          />
          <button
            id="ask-btn"
            className="ask-btn"
            onClick={ask}
            disabled={busy || !repo || !question.trim()}
            title="Send"
          >
            ➜
          </button>
        </div>
      </div>
    </div>
  );
}
