"""Lab environment tools for the Lab Orchestrator agent.

Provides code execution, shell commands, and structured architecture
review capabilities for implementation consulting.
"""

from __future__ import annotations

import io
import json
import logging
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout

from strands import tool

logger = logging.getLogger(__name__)

_SHELL_TIMEOUT = 60
_ALLOWED_SHELL_COMMANDS = frozenset({
    "ls", "cat", "head", "tail", "find", "grep", "wc",
    "tree", "pwd", "echo", "date", "whoami",
    "docker", "terraform", "kubectl", "helm",
    "git", "aws", "pip", "python",
})


@tool
def python_repl(code: str) -> str:
    """Execute Python code in an isolated namespace and return the output.

    Useful for quick computations, data transformations, generating code
    snippets, or testing logic. The execution is sandboxed to the current
    process with captured stdout/stderr.

    Args:
        code: Python code to execute.

    Returns:
        Combined stdout and stderr output, or error traceback.
    """
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    namespace: dict = {}

    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(code, namespace)  # noqa: S102
    except Exception as exc:
        stderr_buf.write(f"\nException: {type(exc).__name__}: {exc}")

    output = stdout_buf.getvalue()
    errors = stderr_buf.getvalue()

    result_parts: list[str] = []
    if output:
        result_parts.append(f"STDOUT:\n{output}")
    if errors:
        result_parts.append(f"STDERR:\n{errors}")
    if not result_parts:
        result_parts.append("(no output)")

    return "\n".join(result_parts)


@tool
def shell_exec(command: str, working_dir: str = ".") -> str:
    """Execute a shell command and return its output.

    The command is validated against an allowlist of safe base commands.
    Use for inspecting infrastructure state, running terraform plans,
    checking git status, listing files, etc.

    Args:
        command: The shell command to run.
        working_dir: Working directory for the command (default: current dir).

    Returns:
        Combined stdout/stderr output, or an error message.
    """
    base_cmd = command.strip().split()[0] if command.strip() else ""
    if base_cmd not in _ALLOWED_SHELL_COMMANDS:
        return (
            f"ERROR: Command '{base_cmd}' is not in the allowlist.\n"
            f"Allowed commands: {', '.join(sorted(_ALLOWED_SHELL_COMMANDS))}"
        )

    try:
        result = subprocess.run(
            command,
            shell=True,  # noqa: S602
            capture_output=True,
            text=True,
            timeout=_SHELL_TIMEOUT,
            cwd=working_dir,
        )
    except subprocess.TimeoutExpired:
        return f"ERROR: Command timed out after {_SHELL_TIMEOUT}s"
    except OSError as exc:
        return f"ERROR: Failed to execute command: {exc}"

    parts: list[str] = []
    if result.stdout:
        parts.append(result.stdout)
    if result.stderr:
        parts.append(f"STDERR:\n{result.stderr}")
    if result.returncode != 0:
        parts.append(f"Exit code: {result.returncode}")
    if not parts:
        parts.append("(no output)")

    return "\n".join(parts)


@tool
def architecture_review(
    component_name: str,
    description: str,
    tech_stack: list[str],
    constraints: list[str] | None = None,
    current_architecture: str | None = None,
) -> str:
    """Generate a structured architecture review document for a component.

    Produces a standardized review template that the Lab Orchestrator agent
    can populate and reason over. This tool structures the input; the agent
    provides the analysis.

    Args:
        component_name: Name of the component or system being reviewed.
        description: What this component does and why it exists.
        tech_stack: Technologies involved (e.g., ['Kubernetes', 'Vault', 'Terraform']).
        constraints: Optional list of constraints or requirements.
        current_architecture: Optional description of the current state.

    Returns:
        A structured architecture review document in markdown format.
    """
    review = {
        "component": component_name,
        "description": description,
        "tech_stack": tech_stack,
        "constraints": constraints or [],
        "current_architecture": current_architecture or "Not specified",
        "review_sections": [
            "## Strengths",
            "## Risks & Concerns",
            "## Recommended Changes",
            "## Implementation Roadmap",
            "## Dependencies & Integration Points",
        ],
    }

    md_lines = [
        f"# Architecture Review: {component_name}",
        "",
        f"**Description:** {description}",
        "",
        f"**Tech Stack:** {', '.join(tech_stack)}",
        "",
    ]

    if constraints:
        md_lines.append("**Constraints:**")
        for c in constraints:
            md_lines.append(f"- {c}")
        md_lines.append("")

    if current_architecture:
        md_lines.append(f"**Current Architecture:** {current_architecture}")
        md_lines.append("")

    for section in review["review_sections"]:
        md_lines.append(section)
        md_lines.append("")
        md_lines.append("*(Agent analysis goes here)*")
        md_lines.append("")

    return "\n".join(md_lines)
