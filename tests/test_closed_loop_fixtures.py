"""Closed-loop fixture tests for DiagnosticEnvelope/v1 contract.

These tests verify that the agent CLI produces stable DiagnosticEnvelope/v1
JSON output against golden fixtures, including valid inputs, invalid inputs,
and log files.
"""

from __future__ import annotations

import json
from pathlib import Path

from mlip_lsp import tool

FIXTURES = Path(__file__).parent / "fixtures"

# Required fields in DiagnosticEnvelope/v1 diagnostics
REQUIRED_DIAGNOSTIC_FIELDS = {
    "code",
    "severity",
    "category",
    "confidence",
    "source",
    "range",
    "software",
    "file_type",
    "path",
    "fix_hints",
    "blocking",
}

# Required fields in the agent check payload
REQUIRED_PAYLOAD_FIELDS = {
    "uri",
    "operation",
    "ok",
    "version",
    "software",
    "diagnostic_engine",
    "diagnostic_envelope",
    "diagnostics",
    "summary",
}


class TestClosedLoopValidFixtures:
    """Tests for valid fixtures that should produce clean output."""

    def test_valid_manifest_json_produces_envelope_v1(self, capsys) -> None:
        """Valid JSON manifest should produce DiagnosticEnvelope/v1 with no blocking diagnostics."""
        rc = tool.main(["check", str(FIXTURES / "valid" / "manifest.json")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)

        # Verify envelope shape
        for field in REQUIRED_PAYLOAD_FIELDS:
            assert field in payload, f"Missing required payload field: {field}"

        assert payload["diagnostic_envelope"] == "v1"
        assert payload["diagnostic_engine"] == "1.0"
        assert payload["software"] == "mlip"
        assert payload["ok"] is True
        assert payload["operation"] == "check"

        # Verify diagnostics are clean
        assert payload["summary"]["blocking"] == 0
        assert payload["summary"]["errors"] == 0

    def test_valid_manifest_yaml_produces_envelope_v1(self, capsys) -> None:
        """Valid YAML manifest should produce DiagnosticEnvelope/v1 with no blocking diagnostics."""
        rc = tool.main(["check", str(FIXTURES / "valid" / "manifest.yaml")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)

        assert payload["diagnostic_envelope"] == "v1"
        assert payload["ok"] is True
        assert payload["summary"]["blocking"] == 0

    def test_valid_script_produces_envelope_v1(self, capsys) -> None:
        """Valid Python script should produce DiagnosticEnvelope/v1 with no blocking diagnostics."""
        rc = tool.main(["check", str(FIXTURES / "valid" / "valid_script.py")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)

        assert payload["diagnostic_envelope"] == "v1"
        assert payload["ok"] is True


class TestClosedLoopInvalidFixtures:
    """Tests for invalid fixtures that should produce blocking diagnostics."""

    def test_missing_model_produces_blocking_error(self, capsys) -> None:
        """Missing model key should produce a blocking error diagnostic."""
        rc = tool.main(
            [
                "check",
                "--fail-on-blocking",
                str(FIXTURES / "invalid" / "missing_model.json"),
            ]
        )
        # Should return non-zero because of blocking diagnostic
        assert rc == 1
        payload = json.loads(capsys.readouterr().out)

        assert payload["diagnostic_envelope"] == "v1"
        assert payload["ok"] is False
        assert payload["summary"]["blocking"] > 0
        assert payload["summary"]["errors"] > 0

        # Verify diagnostic has required fields
        for diag in payload["diagnostics"]:
            for field in REQUIRED_DIAGNOSTIC_FIELDS:
                assert field in diag, f"Missing required diagnostic field: {field}"

        # Verify specific error code
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "MLIP-E082" in codes, f"Expected MLIP-E082 in codes: {codes}"

    def test_missing_model_yaml_produces_blocking_error(self, capsys) -> None:
        """Missing model key in YAML should produce a blocking error diagnostic."""
        rc = tool.main(
            [
                "check",
                "--fail-on-blocking",
                str(FIXTURES / "invalid" / "missing_model.yaml"),
            ]
        )
        assert rc == 1
        payload = json.loads(capsys.readouterr().out)

        assert payload["diagnostic_envelope"] == "v1"
        assert payload["ok"] is False
        assert payload["summary"]["blocking"] > 0

    def test_invalid_json_produces_syntax_error(self, capsys) -> None:
        """Invalid JSON should produce a syntax error diagnostic."""
        rc = tool.main(
            [
                "check",
                "--fail-on-blocking",
                str(FIXTURES / "invalid" / "invalid_json.json"),
            ]
        )
        assert rc == 1
        payload = json.loads(capsys.readouterr().out)

        assert payload["diagnostic_envelope"] == "v1"
        assert payload["ok"] is False

        # Verify syntax error code
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "MLIP-E080" in codes, f"Expected MLIP-E080 in codes: {codes}"


class TestClosedLoopLogFixtures:
    """Tests for log fixtures that should produce log diagnostics."""

    def test_clean_log_produces_no_traceback_diagnostics(self, capsys) -> None:
        """Clean log should produce no traceback diagnostics."""
        rc = tool.main(["check", str(FIXTURES / "logs" / "clean.log")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)

        assert payload["diagnostic_envelope"] == "v1"

        # No traceback diagnostics
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "MLIP-E087" not in codes, f"Unexpected MLIP-E087 in codes: {codes}"

    def test_traceback_log_produces_traceback_diagnostic(self, capsys) -> None:
        """Log with traceback should produce a traceback diagnostic."""
        rc = tool.main(
            [
                "check",
                "--fail-on-blocking",
                str(FIXTURES / "logs" / "traceback.log"),
            ]
        )
        # Should return non-zero because of error diagnostic
        assert rc == 1
        payload = json.loads(capsys.readouterr().out)

        assert payload["diagnostic_envelope"] == "v1"
        assert payload["ok"] is False

        # Verify traceback error code
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "MLIP-E087" in codes, f"Expected MLIP-E087 in codes: {codes}"


class TestClosedLoopFixPreview:
    """Tests for fix preview actions."""

    def test_fix_returns_actions_for_blocking_diagnostic(self, capsys) -> None:
        """Fix operation should return actions for blocking diagnostics."""
        rc = tool.main(["fix", str(FIXTURES / "invalid" / "missing_model.json")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)

        assert payload["diagnostic_envelope"] == "v1"
        assert payload["operation"] == "fix"
        assert "actions" in payload
        assert len(payload["actions"]) > 0

        # Verify action shape
        for action in payload["actions"]:
            assert "title" in action
            assert "kind" in action
            assert "diagnostic_code" in action
            assert "blocking" in action
            assert "safe_to_auto_apply" in action

    def test_fix_returns_actions_for_syntax_error(self, capsys) -> None:
        """Fix operation should return actions for syntax errors."""
        rc = tool.main(["fix", str(FIXTURES / "invalid" / "invalid_json.json")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)

        assert "actions" in payload
        assert len(payload["actions"]) > 0


class TestClosedLoopPreflight:
    """Tests for preflight operation with fixtures."""

    def test_preflight_valid_workspace_produces_envelope(self, capsys) -> None:
        """Preflight on valid workspace should produce DiagnosticEnvelope/v1."""
        rc = tool.main(["preflight", str(FIXTURES / "preflight" / "valid_manifest")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)

        assert payload["diagnostic_envelope"] == "v1"
        assert payload["operation"] == "preflight"
        assert payload["ok"] is True
        assert payload["summary"]["blocking"] == 0

    def test_preflight_invalid_workspace_produces_blocking(self, capsys) -> None:
        """Preflight on invalid workspace should produce blocking diagnostics."""
        rc = tool.main(
            [
                "preflight",
                "--fail-on-blocking",
                str(FIXTURES / "preflight" / "missing_model_potential"),
            ]
        )
        # Should return non-zero because of blocking diagnostic
        assert rc == 1
        payload = json.loads(capsys.readouterr().out)

        assert payload["diagnostic_envelope"] == "v1"
        assert payload["ok"] is False
        assert payload["summary"]["blocking"] > 0


class TestClosedLoopOpenQC:
    """Tests for OpenQC smoke evidence."""

    def test_capabilities_payload_has_openqc_fields(self) -> None:
        """Capabilities payload should have OpenQC compatibility fields."""
        payload = tool._capabilities_payload()

        assert payload["schema"] == "OpenQCLspCapabilities"
        assert payload["version"] == 1
        assert payload["software"] == "mlip"
        assert "openqc" in payload

        openqc = payload["openqc"]
        assert "registryId" in openqc
        assert "repoName" in openqc
        assert "contextContract" in openqc
        assert "diagnosticEnvelope" in openqc
        assert openqc["diagnosticEnvelope"] == "DiagnosticEnvelope/v1"

    def test_capabilities_payload_has_required_capabilities(self) -> None:
        """Capabilities payload should list required capabilities."""
        payload = tool._capabilities_payload()

        required_capabilities = {
            "agent-envelope",
            "agent-json-cli",
            "blocking-gate",
            "diagnostics",
            "rich-diagnostics",
            "diagnostic-engine-v1",
            "source-provenance",
        }
        assert required_capabilities <= set(payload["capabilities"])

    def test_capabilities_payload_has_agent_cli(self) -> None:
        """Capabilities payload should describe agent CLI."""
        payload = tool._capabilities_payload()

        assert "agentCli" in payload
        agent_cli = payload["agentCli"]
        assert "command" in agent_cli
        assert "operations" in agent_cli
        assert "check" in agent_cli["operations"]
        assert "fix" in agent_cli["operations"]
        assert agent_cli["jsonFormat"] is True
        assert agent_cli["failOnBlocking"] is True


class TestClosedLoopDiagnosticEnvelopeV1Contract:
    """Tests that verify the full DiagnosticEnvelope/v1 contract."""

    def test_all_diagnostics_have_required_fields(self, capsys) -> None:
        """All diagnostics from any fixture must have required envelope fields."""
        # Test with invalid fixture that produces diagnostics
        tool.main(["check", str(FIXTURES / "invalid" / "missing_model.json")])
        payload = json.loads(capsys.readouterr().out)

        for diag in payload["diagnostics"]:
            for field in REQUIRED_DIAGNOSTIC_FIELDS:
                assert field in diag, f"Missing required diagnostic field: {field}"

            # Verify field types
            assert isinstance(diag["code"], str)
            assert isinstance(diag["severity"], str)
            assert isinstance(diag["category"], str)
            assert isinstance(diag["confidence"], (int, float))
            assert isinstance(diag["source"], str)
            assert isinstance(diag["blocking"], bool)
            assert isinstance(diag["fix_hints"], list)

            # Verify severity is valid
            assert diag["severity"] in {"error", "warning", "information", "hint"}

            # Verify range structure
            assert "start" in diag["range"]
            assert "end" in diag["range"]
            assert "line" in diag["range"]["start"]
            assert "character" in diag["range"]["start"]

    def test_payload_summary_matches_diagnostics(self, capsys) -> None:
        """Payload summary should match actual diagnostic counts."""
        tool.main(["check", str(FIXTURES / "invalid" / "missing_model.json")])
        payload = json.loads(capsys.readouterr().out)

        diagnostics = payload["diagnostics"]
        summary = payload["summary"]

        assert summary["count"] == len(diagnostics)
        assert summary["errors"] == sum(1 for d in diagnostics if d["severity"] == "error")
        assert summary["warnings"] == sum(1 for d in diagnostics if d["severity"] == "warning")
        assert summary["blocking"] == sum(1 for d in diagnostics if d["blocking"])
