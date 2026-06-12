"""Runtime log parser for MLIP workflows.

Detects Python tracebacks and other runtime artifacts in log output.
Emits MLIP-E087 diagnostics for each traceback found.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..diagnostics import Diagnostic

# Regex that matches the start of a Python traceback line
_TRACEBACK_RE = re.compile(r"^Traceback \(most recent call last\)", re.MULTILINE)
_ERROR_LINE_RE = re.compile(r"^(\w+Error|Exception): (.+)$", re.MULTILINE)


@dataclass(frozen=True)
class TracebackBlock:
    """A single traceback extracted from a log."""
    start_line: int
    error_type: str
    error_message: str


def parse_log(content: str) -> list[TracebackBlock]:
    """Extract all traceback blocks from log content."""
    blocks: list[TracebackBlock] = []
    for match in _TRACEBACK_RE.finditer(content):
        start_line = content[:match.start()].count("\n") + 1
        # Find the error line after the traceback header
        rest = content[match.end():]
        error_type = "Error"
        error_message = "unknown error"
        err_match = _ERROR_LINE_RE.search(rest)
        if err_match:
            error_type = err_match.group(1)
            error_message = err_match.group(2)
        blocks.append(
            TracebackBlock(
                start_line=start_line,
                error_type=error_type,
                error_message=error_message,
            )
        )
    return blocks


def log_diagnostics(
    content: str, file_path: str
) -> list[Diagnostic]:
    """Produce diagnostics for a runtime log file.

    Returns MLIP-E087 for each Python traceback found.
    """
    blocks = parse_log(content)
    diagnostics: list[Diagnostic] = []
    for block in blocks:
        diagnostics.append(
            Diagnostic(
                code="MLIP-E087",
                severity="error",
                message=(
                    f"runtime log contains a Python traceback "
                    f"({block.error_type}: {block.error_message}) "
                    f"starting at line {block.start_line}"
                ),
                file=file_path,
                line=block.start_line,
                evidence=[
                    f"Traceback detected: {block.error_type}: {block.error_message}",
                ],
                suggested_fix={
                    "kind": "investigate_traceback",
                    "error_type": block.error_type,
                    "error_message": block.error_message,
                },
                confidence=0.95,
            )
        )
    return diagnostics
