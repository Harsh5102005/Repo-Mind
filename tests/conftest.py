"""Pytest configuration for RepoMind tests."""

import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import pytest


@pytest.fixture
def tmp_path_factory():
    """Provide tmp_path factory."""
    return pytest.TempPathFactory()