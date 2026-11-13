"""Cloner for RepoMind (Phase 1).

GitHub URL in -> local folder out, plus a list of the Python files
inside it (junk folders skipped).
"""

import shutil
import subprocess
from pathlib import Path
from typing import List
from urllib.parse import urlparse

# Where cloned repos live: <project-root>/data/repos
REPOS_DIR = Path(__file__).resolve().parents[3] / "data" / "repos"

# Folders we never want to chunk
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".idea", ".vscode"}


def repo_name_from_url(url: str) -> str:
    """'https://github.com/user/repo.git' -> 'repo'."""
    path = urlparse(url).path.strip("/")
    name = path.split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name


def clone_repo(url: str, dest_dir: Path = None) -> Path:
    """Shallow-clone a repo (latest commit only, much faster).
    If the folder already exists, it is removed first so every
    ingest starts from fresh code."""
    name = repo_name_from_url(url)
    dest = Path(dest_dir) if dest_dir else REPOS_DIR / name
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Cloning {url} ...")
    subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        check=True,
        capture_output=True,
        text=True,
    )
    print(f"Cloned to {dest}")
    return dest


def list_python_files(root: Path) -> List[Path]:
    """All .py files under root, skipping junk folders."""
    files = []
    for path in Path(root).rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


if __name__ == "__main__":
    # Test: clone your own Video Analyzer repo and list its files.
    url = "https://github.com/Harsh5102005/Ai-Video-Content-Analyzer"
    folder = clone_repo(url)
    py_files = list_python_files(folder)
    print(f"\nFound {len(py_files)} Python files:")
    for f in py_files:
        print(f"  {f.relative_to(folder)}")
