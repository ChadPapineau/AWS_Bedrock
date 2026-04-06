"""Tests for the Lab Orchestrator agent and its lab tools."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.tools.lab_tools import python_repl, shell_exec, architecture_review


class TestPythonRepl:
    def test_captures_stdout(self):
        result = python_repl.fn(code="print('hello from repl')")
        assert "hello from repl" in result

    def test_captures_expression_via_print(self):
        result = python_repl.fn(code="x = 2 + 2\nprint(f'result: {x}')")
        assert "result: 4" in result

    def test_captures_exceptions(self):
        result = python_repl.fn(code="raise ValueError('test error')")
        assert "ValueError" in result
        assert "test error" in result

    def test_no_output_message(self):
        result = python_repl.fn(code="x = 42")
        assert "no output" in result

    def test_captures_stderr(self):
        result = python_repl.fn(code="import sys; sys.stderr.write('warning\\n')")
        assert "STDERR" in result
        assert "warning" in result


class TestShellExec:
    def test_runs_allowed_command(self):
        result = shell_exec.fn(command="echo 'hello shell'")
        assert "hello shell" in result

    def test_blocks_disallowed_command(self):
        result = shell_exec.fn(command="rm -rf /")
        assert "ERROR" in result
        assert "not in the allowlist" in result

    def test_returns_exit_code_on_failure(self):
        result = shell_exec.fn(command="ls /nonexistent_directory_xyz")
        assert "Exit code" in result or "No such file" in result

    def test_allowed_commands_include_common_tools(self):
        result = shell_exec.fn(command="pwd")
        assert "/" in result


class TestArchitectureReview:
    def test_generates_structured_review(self):
        result = architecture_review.fn(
            component_name="Secrets Rotation Service",
            description="Automated rotation of database credentials via Vault",
            tech_stack=["HashiCorp Vault", "AWS Lambda", "PostgreSQL"],
            constraints=["Must complete rotation within 30 seconds", "Zero downtime"],
            current_architecture="Manual rotation via runbook",
        )

        assert "Secrets Rotation Service" in result
        assert "HashiCorp Vault" in result
        assert "Strengths" in result
        assert "Risks & Concerns" in result
        assert "Recommended Changes" in result
        assert "Implementation Roadmap" in result
        assert "30 seconds" in result
        assert "Manual rotation" in result

    def test_handles_minimal_input(self):
        result = architecture_review.fn(
            component_name="Test Component",
            description="A test",
            tech_stack=["Python"],
        )

        assert "Test Component" in result
        assert "Python" in result
        assert "Not specified" in result
