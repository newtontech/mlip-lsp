from __future__ import annotations

from pathlib import Path

from mlip_lsp.analyzer import analyze_path, format_text


def test_valid_fixture_has_no_errors(tmp_path: Path) -> None:
    fixture = tmp_path / "mlip_submit.json"
    fixture.write_text(
        '{"model":"DPA3.1-3M","structure":"input.cif","task":"optimize"}\n', encoding="utf-8"
    )

    diagnostics = analyze_path(tmp_path)

    assert not [item for item in diagnostics if item.severity == "error"]


def test_invalid_fixture_reports_diagnostic(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.json"
    fixture.write_text('{"model":"DPA3.1-3M"}\n', encoding="utf-8")

    diagnostics = analyze_path(tmp_path)

    assert diagnostics


def test_formatter_is_idempotent() -> None:
    first = format_text('{"model":"DPA3.1-3M","structure":"input.cif","task":"optimize"}\n')
    second = format_text(first)

    assert second == first
