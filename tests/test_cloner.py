"""Tests for RepoMind cloner."""

from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.app.ingest.cloner import repo_name_from_url, list_python_files, SKIP_DIRS


def test_repo_name_from_url():
    """Test extracting repo name from various GitHub URL formats."""
    assert repo_name_from_url("https://github.com/user/repo") == "repo"
    assert repo_name_from_url("https://github.com/user/repo.git") == "repo"
    assert repo_name_from_url("https://github.com/user/repo/") == "repo"
    assert repo_name_from_url("git@github.com:user/repo.git") == "repo"
    assert repo_name_from_url("https://github.com/org/subgroup/repo") == "repo"


def test_list_python_files_skips_junk_dirs(tmp_path: Path):
    """Test that list_python_files skips configured junk directories."""
    # Create structure with junk dirs
    (tmp_path / "main.py").write_text("print('main')")
    (tmp_path / "module").mkdir()
    (tmp_path / "module" / "core.py").write_text("print('core')")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "main.cpython-311.pyc").write_bytes(b"")
    (tmp_path / "venv").mkdir()
    (tmp_path / "venv" / "lib.py").write_text("print('venv')")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg.py").write_text("print('node')")

    files = list_python_files(tmp_path)
    file_names = {f.name for f in files}

    # Should find main.py and module/core.py
    assert "main.py" in file_names
    assert "core.py" in file_names

    # Should NOT find files in skip dirs
    assert "config" not in file_names
    assert "lib.py" not in file_names
    assert "pkg.py" not in file_names


def test_list_python_files_sorted(tmp_path: Path):
    """Test that files are returned in sorted order."""
    (tmp_path / "zebra.py").write_text("")
    (tmp_path / "alpha.py").write_text("")
    (tmp_path / "beta.py").write_text("")

    files = list_python_files(tmp_path)
    assert [f.name for f in files] == ["alpha.py", "beta.py", "zebra.py"]


def test_skip_dirs_constant():
    """Verify SKIP_DIRS contains expected directories."""
    expected = {".git", "__pycache__", ".venv", "venv", "node_modules", ".idea", ".vscode"}
    assert SKIP_DIRS == expected


if __name__ == "__main__":
    test_repo_name_from_url()
    print("All tests passed!")