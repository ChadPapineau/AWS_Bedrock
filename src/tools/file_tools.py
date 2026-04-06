"""File I/O tools for the Planning agent.

Provides file read/write capabilities for managing local knowledge base
documents and persisting contextualized plans.
"""

from __future__ import annotations

import logging
from pathlib import Path

from strands import tool

logger = logging.getLogger(__name__)

_KNOWLEDGE_BASE_DIR = Path("knowledge_base")


def _resolve_path(filepath: str) -> Path:
    """Resolve a filepath relative to the knowledge base directory, preventing path traversal."""
    resolved = (_KNOWLEDGE_BASE_DIR / filepath).resolve()
    base = _KNOWLEDGE_BASE_DIR.resolve()
    if not str(resolved).startswith(str(base)):
        raise ValueError(f"Path traversal detected: {filepath}")
    return resolved


@tool
def file_read(filepath: str) -> str:
    """Read the contents of a file from the local knowledge base.

    Args:
        filepath: Path relative to the knowledge_base/ directory.

    Returns:
        The file contents as a string, or an error message.
    """
    try:
        path = _resolve_path(filepath)
        if not path.exists():
            available = [str(p.relative_to(_KNOWLEDGE_BASE_DIR)) for p in _KNOWLEDGE_BASE_DIR.rglob("*") if p.is_file()]
            return (
                f"File not found: {filepath}\n"
                f"Available files: {', '.join(available) if available else '(none -- knowledge base is empty)'}"
            )
        return path.read_text(encoding="utf-8")
    except ValueError as exc:
        return f"ERROR: {exc}"
    except OSError as exc:
        logger.error("Failed to read %s: %s", filepath, exc)
        return f"ERROR: Could not read file: {exc}"


@tool
def file_write(filepath: str, content: str, mode: str = "overwrite") -> str:
    """Write content to a file in the local knowledge base.

    Args:
        filepath: Path relative to the knowledge_base/ directory.
        content: The content to write.
        mode: 'overwrite' to replace the file, 'append' to add to the end. Default 'overwrite'.

    Returns:
        Confirmation message or error.
    """
    if mode not in ("overwrite", "append"):
        return "ERROR: mode must be 'overwrite' or 'append'"

    try:
        path = _resolve_path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        if mode == "append":
            with path.open("a", encoding="utf-8") as f:
                f.write(content)
        else:
            path.write_text(content, encoding="utf-8")

        logger.info("Wrote %d chars to %s (mode=%s)", len(content), filepath, mode)
        return f"Successfully wrote {len(content)} characters to {filepath}"
    except ValueError as exc:
        return f"ERROR: {exc}"
    except OSError as exc:
        logger.error("Failed to write %s: %s", filepath, exc)
        return f"ERROR: Could not write file: {exc}"
