"""Tests for the Planner agent and its file tools."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import patch

import pytest

from src.tools.file_tools import file_read, file_write, _KNOWLEDGE_BASE_DIR


@pytest.fixture(autouse=True)
def tmp_knowledge_base(tmp_path, monkeypatch):
    """Redirect the knowledge base to a temp directory for test isolation."""
    monkeypatch.setattr("src.tools.file_tools._KNOWLEDGE_BASE_DIR", tmp_path)
    return tmp_path


class TestFileRead:
    def test_reads_existing_file(self, tmp_knowledge_base):
        test_file = tmp_knowledge_base / "notes" / "test.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# Test Content\nHello from the knowledge base.")

        result = file_read.fn(filepath="notes/test.md")
        assert "Test Content" in result
        assert "Hello from the knowledge base" in result

    def test_returns_error_for_missing_file(self, tmp_knowledge_base):
        result = file_read.fn(filepath="nonexistent.md")
        assert "File not found" in result

    def test_lists_available_files_on_miss(self, tmp_knowledge_base):
        (tmp_knowledge_base / "existing.md").write_text("data")
        result = file_read.fn(filepath="missing.md")
        assert "existing.md" in result

    def test_blocks_path_traversal(self, tmp_knowledge_base):
        result = file_read.fn(filepath="../../etc/passwd")
        assert "ERROR" in result


class TestFileWrite:
    def test_writes_new_file(self, tmp_knowledge_base):
        result = file_write.fn(filepath="plans/vault-migration.md", content="# Vault Migration Plan")
        assert "Successfully wrote" in result

        written = (tmp_knowledge_base / "plans" / "vault-migration.md").read_text()
        assert "Vault Migration Plan" in written

    def test_appends_to_existing_file(self, tmp_knowledge_base):
        target = tmp_knowledge_base / "log.txt"
        target.write_text("Line 1\n")

        file_write.fn(filepath="log.txt", content="Line 2\n", mode="append")
        content = target.read_text()
        assert "Line 1" in content
        assert "Line 2" in content

    def test_overwrites_by_default(self, tmp_knowledge_base):
        target = tmp_knowledge_base / "data.txt"
        target.write_text("old content")

        file_write.fn(filepath="data.txt", content="new content")
        assert target.read_text() == "new content"

    def test_rejects_invalid_mode(self):
        result = file_write.fn(filepath="test.txt", content="x", mode="delete")
        assert "ERROR" in result

    def test_creates_parent_directories(self, tmp_knowledge_base):
        file_write.fn(filepath="deep/nested/dir/file.md", content="deep content")
        assert (tmp_knowledge_base / "deep" / "nested" / "dir" / "file.md").exists()

    def test_blocks_path_traversal(self, tmp_knowledge_base):
        result = file_write.fn(filepath="../../etc/evil", content="bad")
        assert "ERROR" in result
