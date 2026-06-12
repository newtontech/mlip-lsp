"""Tests for the runtime log parser (Issue #24: MLIP-E087)."""

from __future__ import annotations

from pathlib import Path

from mlip_lsp.features.log_parser import log_diagnostics, parse_log

FIXTURES = Path(__file__).parent / "fixtures"


class TestParseLog:
    def test_no_traceback(self) -> None:
        content = "All good.\nStep 1: done.\n"
        blocks = parse_log(content)
        assert blocks == []

    def test_single_traceback(self) -> None:
        content = (
            "Starting...\n"
            "Traceback (most recent call last):\n"
            '  File "run.py", line 5, in <module>\n'
            "    calc = MLIPCalculator(model='bad')\n"
            "RuntimeError: Model not found\n"
        )
        blocks = parse_log(content)
        assert len(blocks) == 1
        assert blocks[0].start_line == 2
        assert blocks[0].error_type == "RuntimeError"
        assert blocks[0].error_message == "Model not found"

    def test_multiple_tracebacks(self) -> None:
        content = (
            "Run 1:\n"
            "Traceback (most recent call last):\n"
            "  File 'a.py', line 1\n"
            "ValueError: bad value\n"
            "Run 2:\n"
            "Traceback (most recent call last):\n"
            "  File 'b.py', line 2\n"
            "TypeError: bad type\n"
        )
        blocks = parse_log(content)
        assert len(blocks) == 2
        assert blocks[0].error_type == "ValueError"
        assert blocks[1].error_type == "TypeError"

    def test_traceback_line_number(self) -> None:
        content = "Line 1\nLine 2\nLine 3\nTraceback (most recent call last):\nError: fail\n"
        blocks = parse_log(content)
        assert blocks[0].start_line == 4

    def test_traceback_without_error_line(self) -> None:
        content = "Traceback (most recent call last):\n  some output\n"
        blocks = parse_log(content)
        assert len(blocks) == 1
        assert blocks[0].error_type == "Error"
        assert blocks[0].error_message == "unknown error"


class TestLogDiagnostics:
    def test_clean_log_no_diagnostics(self) -> None:
        content = "Starting...\nStep 1: done\n"
        diags = log_diagnostics(content, "run.log")
        assert diags == []

    def test_traceback_produces_e087(self) -> None:
        content = (
            "Traceback (most recent call last):\n"
            "  File 'run.py', line 5\n"
            "RuntimeError: model not found\n"
        )
        diags = log_diagnostics(content, "run.log")
        assert len(diags) == 1
        assert diags[0].code == "MLIP-E087"
        assert diags[0].severity == "error"
        assert "traceback" in diags[0].message.lower()
        assert diags[0].confidence >= 0.9

    def test_e087_has_suggested_fix(self) -> None:
        content = "Traceback (most recent call last):\nValueError: bad\n"
        diags = log_diagnostics(content, "run.log")
        assert diags[0].suggested_fix is not None
        assert diags[0].suggested_fix["kind"] == "investigate_traceback"

    def test_e087_has_evidence(self) -> None:
        content = "Traceback (most recent call last):\nTypeError: wrong type\n"
        diags = log_diagnostics(content, "run.log")
        assert diags[0].evidence
        assert "TypeError" in diags[0].evidence[0]

    def test_clean_log_fixture(self) -> None:
        content = (FIXTURES / "clean.log").read_text(encoding="utf-8")
        diags = log_diagnostics(content, str(FIXTURES / "clean.log"))
        assert diags == []

    def test_traceback_log_fixture(self) -> None:
        content = (FIXTURES / "traceback.log").read_text(encoding="utf-8")
        diags = log_diagnostics(content, str(FIXTURES / "traceback.log"))
        assert len(diags) == 1
        assert diags[0].code == "MLIP-E087"
        assert "RuntimeError" in diags[0].message
