"""Tests for MLIP diagnostic rules (MLIP-prefixed codes)."""

from __future__ import annotations

from mlip_lsp.features.rules import RULES, Rule, format_message, get_rule


class TestRuleDefinitions:
    def test_all_rules_defined(self) -> None:
        expected_codes = {
            "MLIP-E080",
            "MLIP-E081",
            "MLIP-E082",
            "MLIP-E083",
            "MLIP-E084",
            "MLIP-W080",
            "MLIP-E085",
            "MLIP-E086",
            "MLIP-E087",
        }
        assert set(RULES.keys()) == expected_codes

    def test_rule_fields(self) -> None:
        for code, rule in RULES.items():
            assert isinstance(rule, Rule)
            assert rule.code == code
            assert rule.severity in ("error", "warning")
            assert rule.name
            assert rule.message_template
            assert rule.category

    def test_get_rule_existing(self) -> None:
        rule = get_rule("MLIP-E080")
        assert rule is not None
        assert rule.name == "mlip.json.invalid"

    def test_get_rule_nonexistent(self) -> None:
        assert get_rule("MLIP-XXX") is None

    def test_format_message_with_params(self) -> None:
        msg = format_message("MLIP-E080", detail="unexpected token")
        assert "unexpected token" in msg
        assert "JSON" in msg

    def test_format_message_e081(self) -> None:
        msg = format_message("MLIP-E081", detail="bad indentation")
        assert "bad indentation" in msg
        assert "YAML" in msg

    def test_format_message_e087(self) -> None:
        msg = format_message("MLIP-E087", line="42")
        assert "42" in msg
        assert "traceback" in msg.lower()

    def test_format_message_unknown(self) -> None:
        msg = format_message("UNKNOWN", detail="fallback")
        assert msg == "fallback"

    def test_error_codes_have_error_severity(self) -> None:
        error_codes = {
            "MLIP-E080",
            "MLIP-E081",
            "MLIP-E082",
            "MLIP-E083",
            "MLIP-E084",
            "MLIP-E085",
            "MLIP-E087",
        }
        for code in error_codes:
            assert RULES[code].severity == "error", f"{code} should be error"

    def test_warning_codes_have_warning_severity(self) -> None:
        warning_codes = {"MLIP-W080", "MLIP-E086"}
        for code in warning_codes:
            assert RULES[code].severity == "warning", f"{code} should be warning"

    def test_rule_categories(self) -> None:
        assert RULES["MLIP-E080"].category == "syntax"
        assert RULES["MLIP-E081"].category == "syntax"
        assert RULES["MLIP-E082"].category == "schema"
        assert RULES["MLIP-E086"].category == "cross-file reference"
        assert RULES["MLIP-E087"].category == "preflight/runtime-risk"
