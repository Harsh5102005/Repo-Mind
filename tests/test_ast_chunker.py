"""Tests for RepoMind AST chunker."""

import tempfile
from pathlib import Path

from backend.app.ingest.ast_chunker import chunk_file


def test_chunk_file_simple():
    """Test chunking a simple Python file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
def hello():
    '''Say hello.'''
    return "Hello, World!"

class MyClass:
    def method(self):
        return 42
""")
        f.flush()
        chunks = chunk_file(Path(f.name))

    assert len(chunks) > 0
    # Check we got both function and class
    symbols = {c["symbol_name"] for c in chunks}
    assert "hello" in symbols
    assert "MyClass" in symbols
    assert "method" in symbols


def test_chunk_file_with_nested():
    """Test chunking with nested functions/classes."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
def outer():
    def inner():
        return 1
    return inner()

class Outer:
    class Inner:
        pass
""")
        f.flush()
        chunks = chunk_file(Path(f.name))

    symbols = {c["symbol_name"] for c in chunks}
    assert "outer" in symbols
    assert "inner" in symbols
    assert "Outer" in symbols
    assert "Inner" in symbols


def test_chunk_file_empty():
    """Test chunking an empty file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        f.flush()
        chunks = chunk_file(Path(f.name))
    assert chunks == []


if __name__ == "__main__":
    test_chunk_file_simple()
    test_chunk_file_with_nested()
    test_chunk_file_empty()
    print("All tests passed!")