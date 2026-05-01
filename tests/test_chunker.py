"""Unit tests for the StructuralChunker in code_chatbot/ingestion/chunker.py."""

import os
import pytest
from code_chatbot.ingestion.chunker import StructuralChunker


def test_chunker_on_python_file():
    """Chunker should return at least one chunk for a real Python file."""
    chunker = StructuralChunker(max_tokens=800)
    file_path = os.path.join(os.path.dirname(__file__), "../app.py")
    with open(file_path, "r") as f:
        content = f.read()
    chunks = chunker.chunk(content, file_path)
    assert len(chunks) >= 1


def test_chunker_on_markdown_file():
    """Chunker should return at least one chunk for a markdown file."""
    chunker = StructuralChunker(max_tokens=800)
    file_path = os.path.join(os.path.dirname(__file__), "../README.md")
    with open(file_path, "r") as f:
        content = f.read()
    chunks = chunker.chunk(content, file_path)
    assert len(chunks) >= 1


def test_chunker_typescript():
    """Chunker should handle TypeScript files."""
    chunker = StructuralChunker(max_tokens=800)
    file_path = os.path.join(os.path.dirname(__file__), "assets/sample-script.ts")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
        chunks = chunker.chunk(content, file_path)
        assert len(chunks) >= 1


def test_chunker_empty_content():
    """Chunker should handle empty content gracefully."""
    chunker = StructuralChunker(max_tokens=800)
    chunks = chunker.chunk("", "empty.py")
    assert isinstance(chunks, list)


if __name__ == "__main__":
    pytest.main()
