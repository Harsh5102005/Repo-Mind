"""Tests for RepoMind API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.app.main import app


client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_repos_empty():
    """Test listing repos when none exist."""
    with patch("backend.app.main.REPOS_DIR.exists", return_value=False):
        response = client.get("/repos")
        assert response.status_code == 200
        assert response.json() == {"repos": []}


def test_ingest_missing_url():
    """Test ingest with missing repo_url."""
    response = client.post("/ingest", json={})
    assert response.status_code == 422  # Validation error


def test_ask_missing_fields():
    """Test ask endpoint with missing required fields."""
    response = client.post("/ask", json={})
    assert response.status_code == 422


def test_ask_missing_repo():
    """Test ask endpoint with missing repo_name."""
    response = client.post("/ask", json={"question": "test"})
    assert response.status_code == 422


def test_ask_missing_question():
    """Test ask endpoint with missing question."""
    response = client.post("/ask", json={"repo_name": "test"})
    assert response.status_code == 422


@patch("backend.app.main.clone_repo")
@patch("backend.app.main.list_python_files")
@patch("backend.app.main.chunk_file")
@patch("backend.app.main.add_chunks")
@patch("backend.app.main.delete_collection")
def test_ingest_success(mock_delete, mock_add_chunks, mock_chunk, mock_list, mock_clone):
    """Test successful ingest flow."""
    # Setup mocks
    mock_clone.return_value = MagicMock()
    mock_list.return_value = [MagicMock(), MagicMock()]
    mock_chunk.return_value = [{"content": "test", "file_path": "test.py", "symbol_name": "func", "start_line": 1, "end_line": 10}]
    mock_add_chunks.return_value = 5

    response = client.post("/ingest", json={"repo_url": "https://github.com/test/repo"})

    assert response.status_code == 200
    data = response.json()
    assert data["repo_name"] == "repo"
    assert data["files_ingested"] == 2
    assert data["chunks_stored"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])