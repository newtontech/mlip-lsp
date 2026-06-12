"""Tests for safe formatter (Issue #5: format_text idempotence)."""

from __future__ import annotations

import json

from mlip_lsp.features.formatter import (
    format_json,
    format_text,
    format_yaml,
    is_idempotent,
    safe_format,
)


class TestFormatJSON:
    def test_pretty_prints_compact_json(self) -> None:
        text = '{"model":"DPA3.1-3M","structure":"input.cif","task":"optimize"}'
        result = format_json(text)
        # Should be pretty-printed with indentation
        assert "\n" in result
        parsed = json.loads(result)
        assert parsed["model"] == "DPA3.1-3M"

    def test_preserves_already_formatted_json(self) -> None:
        text = json.dumps({"model": "DPA3.1-3M", "structure": "input.cif", "task": "optimize"}, indent=2) + "\n"
        result = format_json(text)
        assert result == text

    def test_invalid_json_returns_original(self) -> None:
        text = '{"model": broken}'
        result = format_json(text)
        assert result == text

    def test_empty_json(self) -> None:
        text = "{}"
        result = format_json(text)
        assert json.loads(result) == {}

    def test_idempotent(self) -> None:
        text = '{"model":"X","structure":"s","task":"t"}'
        first = format_json(text)
        second = format_json(first)
        assert first == second


class TestFormatYAML:
    def test_formats_yaml(self) -> None:
        text = "model: DPA3.1-3M\nstructure: input.cif\ntask: optimize\n"
        result = format_yaml(text)
        assert "DPA3.1-3M" in result

    def test_invalid_yaml_returns_original(self) -> None:
        text = "model: DPA3.1-3M\n  bad_indent: true\n"
        result = format_yaml(text)
        assert result == text

    def test_idempotent(self) -> None:
        text = "model: DPA3.1-3M\nstructure: input.cif\ntask: optimize\n"
        first = format_yaml(text)
        second = format_yaml(first)
        assert first == second


class TestFormatText:
    def test_key_value_alignment(self) -> None:
        text = "cutoff = 5.0\nlambda_1 = 0.1\n"
        result = format_text(text)
        lines = result.strip().split("\n")
        eq_positions = [line.index("=") for line in lines]
        assert eq_positions[0] == eq_positions[1]

    def test_preserves_comments(self) -> None:
        text = "# comment\ncutoff = 5.0\n"
        result = format_text(text)
        assert "# comment" in result

    def test_trailing_newline(self) -> None:
        text = "cutoff = 5.0"
        result = format_text(text)
        assert result.endswith("\n")

    def test_empty_input(self) -> None:
        result = format_text("")
        assert result == "\n"

    def test_idempotent(self) -> None:
        text = "cutoff = 5.0\nlambda_1 = 0.1\n"
        first = format_text(text)
        second = format_text(first)
        assert first == second


class TestSafeFormat:
    def test_dispatches_json(self) -> None:
        text = '{"model":"X"}'
        result = safe_format(text, ".json")
        assert "model" in result

    def test_dispatches_yaml(self) -> None:
        text = "model: X\n"
        result = safe_format(text, ".yaml")
        assert "model" in result

    def test_dispatches_yml(self) -> None:
        text = "model: X\n"
        result = safe_format(text, ".yml")
        assert "model" in result

    def test_dispatches_txt(self) -> None:
        text = "cutoff = 5.0\n"
        result = safe_format(text, ".txt")
        assert "cutoff" in result

    def test_unknown_suffix_uses_text(self) -> None:
        text = "cutoff = 5.0\n"
        result = safe_format(text, ".inp")
        assert "cutoff" in result

    def test_never_raises_on_invalid_json(self) -> None:
        text = '{"model": broken}'
        result = safe_format(text, ".json")
        assert result == text  # Returns original on failure

    def test_never_raises_on_invalid_yaml(self) -> None:
        text = "model: DPA3.1-3M\n  bad_indent: true\n"
        result = safe_format(text, ".yaml")
        assert result == text  # Returns original on failure


class TestIdempotence:
    def test_json_idempotent(self) -> None:
        text = '{"model":"DPA3.1-3M","structure":"input.cif","task":"optimize"}'
        assert is_idempotent(text, ".json")

    def test_yaml_idempotent(self) -> None:
        text = "model: DPA3.1-3M\nstructure: input.cif\ntask: optimize\n"
        assert is_idempotent(text, ".yaml")

    def test_text_idempotent(self) -> None:
        text = "cutoff = 5.0\nlambda_1 = 0.1\n"
        assert is_idempotent(text, ".txt")

    def test_compact_json_becomes_idempotent(self) -> None:
        text = '{"model":"X"}'
        first = safe_format(text, ".json")
        assert is_idempotent(first, ".json")

    def test_malformed_json_still_idempotent(self) -> None:
        # Malformed JSON returns as-is, which is trivially idempotent
        text = '{"model": broken}'
        assert is_idempotent(text, ".json")
