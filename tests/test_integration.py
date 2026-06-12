"""Integration tests covering all 16 issues end-to-end."""

from __future__ import annotations

import json
from pathlib import Path

from mlip_lsp.agent_lsp import AgentLSP
from mlip_lsp.analyzer import analyze_path
from mlip_lsp.diagnostics import Diagnostic
from mlip_lsp.rich_diagnostics import agent_check_payload, diagnostic_to_dict
from mlip_lsp.server import create_server

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Issue #5: Safe formatter and idempotence
# ---------------------------------------------------------------------------


class TestIssue5Formatter:
    def test_json_idempotent(self) -> None:
        text = '{"model":"X","structure":"s","task":"t"}'
        from mlip_lsp.features.formatter import safe_format

        first = safe_format(text, ".json")
        second = safe_format(first, ".json")
        assert first == second

    def test_yaml_idempotent(self) -> None:
        text = "model: X\nstructure: s\ntask: t\n"
        from mlip_lsp.features.formatter import safe_format

        first = safe_format(text, ".yaml")
        second = safe_format(first, ".yaml")
        assert first == second

    def test_malformed_json_returns_original(self) -> None:
        from mlip_lsp.features.formatter import safe_format

        text = '{"model": broken}'
        result = safe_format(text, ".json")
        assert result == text


# ---------------------------------------------------------------------------
# Issue #7: Capability: Hover
# ---------------------------------------------------------------------------


class TestIssue7Hover:
    def test_hover_json_model_key(self) -> None:
        server = create_server()
        content = '{"model":"DPA3.1-3M","structure":"s","task":"t"}'
        result = server.hover("file:///tmp/test.json", content, 0, 2)
        assert result is not None
        assert "model" in result.lower()

    def test_hover_yaml_key(self) -> None:
        server = create_server()
        content = "model: DPA3.1-3M\nstructure: s\ntask: t\n"
        result = server.hover("file:///tmp/test.yaml", content, 0, 2)
        assert result is not None
        assert "model" in result.lower() or "MLIP" in result

    def test_hover_python_atoms(self) -> None:
        server = create_server()
        content = "from ase import Atoms\n"
        result = server.hover("file:///tmp/test.py", content, 0, 18)
        assert result is not None
        assert "Atoms" in result

    def test_hover_python_ase(self) -> None:
        server = create_server()
        content = "from ase import Atoms\n"
        result = server.hover("file:///tmp/test.py", content, 0, 5)
        assert result is not None
        assert "ASE" in result

    def test_hover_returns_none_for_unknown(self) -> None:
        server = create_server()
        content = "x = 42\n"
        result = server.hover("file:///tmp/test.py", content, 0, 0)
        assert result is None


# ---------------------------------------------------------------------------
# Issue #8: MatMaster execution rules
# ---------------------------------------------------------------------------


class TestIssue8MatMaster:
    def test_valid_manifest_passes(self, tmp_path: Path) -> None:
        fixture = tmp_path / "manifest.json"
        fixture.write_text(
            json.dumps(
                {
                    "model": "DPA3.1-3M",
                    "structure": "input.cif",
                    "task": "optimize",
                }
            ),
            encoding="utf-8",
        )
        diags = analyze_path(tmp_path)
        errors = [d for d in diags if d.severity == "error"]
        assert not errors

    def test_unknown_model_warns(self, tmp_path: Path) -> None:
        fixture = tmp_path / "manifest.json"
        fixture.write_text(
            json.dumps(
                {
                    "model": "UnknownModel",
                    "structure": "input.cif",
                    "task": "optimize",
                }
            ),
            encoding="utf-8",
        )
        diags = analyze_path(tmp_path)
        warnings = [d.message for d in diags if "unknown MLIP model" in d.message]
        assert warnings


# ---------------------------------------------------------------------------
# Issue #11: Capability: Agent JSON
# ---------------------------------------------------------------------------


class TestIssue11AgentJSON:
    def test_agent_check_valid(self, tmp_path: Path) -> None:
        fixture = tmp_path / "manifest.json"
        fixture.write_text(
            json.dumps(
                {
                    "model": "DPA3.1-3M",
                    "structure": "input.cif",
                    "task": "optimize",
                }
            ),
            encoding="utf-8",
        )
        agent = AgentLSP.from_path(fixture)
        payload = agent.check()
        assert payload["ok"] is True
        assert payload["software"] == "mlip"
        assert "diagnostics" in payload

    def test_agent_check_invalid_json(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.json"
        fixture.write_text('{"model":}', encoding="utf-8")
        agent = AgentLSP.from_path(fixture)
        payload = agent.check()
        assert payload["ok"] is False
        codes = [d["code"] for d in payload["diagnostics"]]
        assert "MLIP-E080" in codes

    def test_agent_check_yaml(self, tmp_path: Path) -> None:
        fixture = tmp_path / "manifest.yaml"
        fixture.write_text(
            "model: DPA3.1-3M\nstructure: input.cif\ntask: optimize\n",
            encoding="utf-8",
        )
        agent = AgentLSP.from_path(fixture)
        payload = agent.check()
        assert payload["software"] == "mlip"

    def test_agent_from_text(self) -> None:
        agent = AgentLSP.from_text(
            '{"model":"DPA3.1-3M","structure":"s","task":"t"}',
            uri="file:///tmp/test.json",
        )
        payload = agent.check()
        assert "diagnostics" in payload

    def test_agent_context_operation(self) -> None:
        agent = AgentLSP.from_text("test")
        payload = agent.context(line=0, character=0)
        assert payload["operation"] == "context"
        assert "position" in payload

    def test_agent_complete_operation(self) -> None:
        agent = AgentLSP.from_text("test")
        payload = agent.complete(line=0, character=0)
        assert payload["operation"] == "complete"
        assert "items" in payload

    def test_agent_hover_operation(self) -> None:
        agent = AgentLSP.from_text("test")
        payload = agent.hover(line=0, character=0)
        assert payload["operation"] == "hover"
        assert "contents" in payload

    def test_agent_symbols_operation(self) -> None:
        agent = AgentLSP.from_text("test")
        payload = agent.symbols()
        assert payload["operation"] == "symbols"
        assert "items" in payload


# ---------------------------------------------------------------------------
# Issue #13: Capability: Diagnostics
# ---------------------------------------------------------------------------


class TestIssue13Diagnostics:
    def test_json_diagnostics_pipeline(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.json"
        content = '{"model":"X"}'
        diags = server.compute_diagnostics(uri, content)
        codes = {d.code for d in diags}
        assert "MLIP-E083" in codes  # missing task
        assert "MLIP-E084" in codes  # missing structure

    def test_yaml_diagnostics_pipeline(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.yaml"
        content = "model: X\n"
        diags = server.compute_diagnostics(uri, content)
        codes = {d.code for d in diags}
        assert "MLIP-E083" in codes
        assert "MLIP-E084" in codes

    def test_python_diagnostics_pipeline(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.py"
        content = "x = 1\n"
        diags = server.compute_diagnostics(uri, content)
        codes = {d.code for d in diags}
        assert "MLIP-W080" in codes  # missing ase
        assert "MLIP-E085" in codes  # missing structure

    def test_log_diagnostics_pipeline(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.log"
        content = "Traceback (most recent call last):\nRuntimeError: fail\n"
        diags = server.compute_diagnostics(uri, content)
        codes = {d.code for d in diags}
        assert "MLIP-E087" in codes


# ---------------------------------------------------------------------------
# Issue #14: RULE mlip.json.invalid (MLIP-E080)
# ---------------------------------------------------------------------------


class TestIssue14JSONInvalid:
    def test_invalid_json_e080(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.json"
        fixture.write_text('{"model": broken}', encoding="utf-8")
        diags = analyze_path(tmp_path)
        e080 = [d for d in diags if d.code == "MLIP-E080"]
        assert e080
        assert e080[0].severity == "error"

    def test_e080_has_line_number(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.json"
        fixture.write_text('{"model": "ok"\ntrailing}', encoding="utf-8")
        diags = analyze_path(tmp_path)
        e080 = [d for d in diags if d.code == "MLIP-E080"]
        assert e080
        assert e080[0].line >= 1

    def test_e080_via_server(self) -> None:
        server = create_server()
        diags = server.compute_diagnostics("file:///tmp/b.json", '{"x":}')
        e080 = [d for d in diags if d.code == "MLIP-E080"]
        assert e080


# ---------------------------------------------------------------------------
# Issue #15: RULE mlip.yaml.invalid (MLIP-E081)
# ---------------------------------------------------------------------------


class TestIssue15YAMLInvalid:
    def test_invalid_yaml_e081(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.yaml"
        fixture.write_text("model: X\n  bad_indent: true\n", encoding="utf-8")
        diags = analyze_path(tmp_path)
        e081 = [d for d in diags if d.code == "MLIP-E081"]
        assert e081
        assert e081[0].severity == "error"

    def test_e081_via_server(self) -> None:
        server = create_server()
        diags = server.compute_diagnostics("file:///tmp/b.yaml", "model: X\n  bad_indent: true\n")
        e081 = [d for d in diags if d.code == "MLIP-E081"]
        assert e081


# ---------------------------------------------------------------------------
# Issue #16: RULE mlip.manifest.missing_model (MLIP-E082)
# ---------------------------------------------------------------------------


class TestIssue16MissingModel:
    def test_json_missing_model_e082(self, tmp_path: Path) -> None:
        fixture = tmp_path / "manifest.json"
        fixture.write_text(json.dumps({"structure": "s", "task": "t"}), encoding="utf-8")
        diags = analyze_path(tmp_path)
        e082 = [d for d in diags if d.code == "MLIP-E082"]
        assert e082

    def test_yaml_missing_model_e082(self, tmp_path: Path) -> None:
        fixture = tmp_path / "manifest.yaml"
        fixture.write_text("structure: s\ntask: t\n", encoding="utf-8")
        diags = analyze_path(tmp_path)
        e082 = [d for d in diags if d.code == "MLIP-E082"]
        assert e082

    def test_e082_via_server(self) -> None:
        server = create_server()
        diags = server.compute_diagnostics(
            "file:///tmp/test.json",
            json.dumps({"structure": "s", "task": "t"}),
        )
        e082 = [d for d in diags if d.code == "MLIP-E082"]
        assert e082


# ---------------------------------------------------------------------------
# Issue #17: RULE mlip.manifest.missing_task (MLIP-E083)
# ---------------------------------------------------------------------------


class TestIssue17MissingTask:
    def test_json_missing_task_e083(self, tmp_path: Path) -> None:
        fixture = tmp_path / "manifest.json"
        fixture.write_text(json.dumps({"model": "m", "structure": "s"}), encoding="utf-8")
        diags = analyze_path(tmp_path)
        e083 = [d for d in diags if d.code == "MLIP-E083"]
        assert e083

    def test_yaml_missing_task_e083(self, tmp_path: Path) -> None:
        fixture = tmp_path / "manifest.yaml"
        fixture.write_text("model: m\nstructure: s\n", encoding="utf-8")
        diags = analyze_path(tmp_path)
        e083 = [d for d in diags if d.code == "MLIP-E083"]
        assert e083


# ---------------------------------------------------------------------------
# Issue #18: RULE mlip.manifest.missing_structure (MLIP-E084)
# ---------------------------------------------------------------------------


class TestIssue18MissingStructure:
    def test_json_missing_structure_e084(self, tmp_path: Path) -> None:
        fixture = tmp_path / "manifest.json"
        fixture.write_text(json.dumps({"model": "m", "task": "t"}), encoding="utf-8")
        diags = analyze_path(tmp_path)
        e084 = [d for d in diags if d.code == "MLIP-E084"]
        assert e084

    def test_yaml_missing_structure_e084(self, tmp_path: Path) -> None:
        fixture = tmp_path / "manifest.yaml"
        fixture.write_text("model: m\ntask: t\n", encoding="utf-8")
        diags = analyze_path(tmp_path)
        e084 = [d for d in diags if d.code == "MLIP-E084"]
        assert e084


# ---------------------------------------------------------------------------
# Issue #19: RULE mlip.python.missing_ase_import (MLIP-W080)
# ---------------------------------------------------------------------------


class TestIssue19MissingASE:
    def test_missing_ase_w080(self, tmp_path: Path) -> None:
        fixture = tmp_path / "script.py"
        fixture.write_text("structure = [1, 2, 3]\n", encoding="utf-8")
        diags = analyze_path(tmp_path)
        w080 = [d for d in diags if d.code == "MLIP-W080"]
        assert w080
        assert w080[0].severity == "warning"

    def test_ase_import_present_no_w080(self, tmp_path: Path) -> None:
        fixture = tmp_path / "script.py"
        fixture.write_text("from ase import Atoms\nstructure = Atoms()\n", encoding="utf-8")
        diags = analyze_path(tmp_path)
        w080 = [d for d in diags if d.code == "MLIP-W080"]
        assert not w080


# ---------------------------------------------------------------------------
# Issue #20: RULE mlip.python.missing_structure_symbol (MLIP-E085)
# ---------------------------------------------------------------------------


class TestIssue20MissingStructureSymbol:
    def test_missing_structure_e085(self, tmp_path: Path) -> None:
        fixture = tmp_path / "script.py"
        fixture.write_text("from ase import Atoms\natoms = Atoms('Cu')\n", encoding="utf-8")
        diags = analyze_path(tmp_path)
        e085 = [d for d in diags if d.code == "MLIP-E085"]
        assert e085
        assert e085[0].severity == "error"

    def test_structure_present_no_e085(self, tmp_path: Path) -> None:
        fixture = tmp_path / "script.py"
        fixture.write_text("from ase import Atoms\nstructure = Atoms()\n", encoding="utf-8")
        diags = analyze_path(tmp_path)
        e085 = [d for d in diags if d.code == "MLIP-E085"]
        assert not e085


# ---------------------------------------------------------------------------
# Issue #21: RULE mlip.files.missing_path_reference (MLIP-E086)
# ---------------------------------------------------------------------------


class TestIssue21MissingPathRef:
    def test_missing_structure_file_e086(self, tmp_path: Path) -> None:
        fixture = tmp_path / "manifest.json"
        fixture.write_text(
            json.dumps(
                {
                    "model": "DPA3.1-3M",
                    "structure": "nonexistent.xyz",
                    "task": "optimize",
                }
            ),
            encoding="utf-8",
        )
        diags = analyze_path(tmp_path)
        e086 = [d for d in diags if d.code == "MLIP-E086"]
        assert e086

    def test_existing_file_no_e086(self, tmp_path: Path) -> None:
        (tmp_path / "POSCAR").write_text("data", encoding="utf-8")
        fixture = tmp_path / "manifest.json"
        fixture.write_text(
            json.dumps(
                {
                    "model": "DPA3.1-3M",
                    "structure": "POSCAR",
                    "task": "optimize",
                }
            ),
            encoding="utf-8",
        )
        diags = analyze_path(tmp_path)
        e086 = [d for d in diags if d.code == "MLIP-E086"]
        assert not e086

    def test_yaml_missing_file_e086(self, tmp_path: Path) -> None:
        fixture = tmp_path / "manifest.yaml"
        fixture.write_text(
            "model: DPA3.1-3M\nstructure: missing.xyz\ntask: optimize\n",
            encoding="utf-8",
        )
        diags = analyze_path(tmp_path)
        e086 = [d for d in diags if d.code == "MLIP-E086"]
        assert e086


# ---------------------------------------------------------------------------
# Issue #22: RULE mlip.log.traceback (MLIP-E087)
# ---------------------------------------------------------------------------


class TestIssue22Traceback:
    def test_traceback_in_log_e087(self, tmp_path: Path) -> None:
        fixture = tmp_path / "run.log"
        fixture.write_text(
            "Starting...\n"
            "Traceback (most recent call last):\n"
            '  File "run.py", line 5\n'
            "RuntimeError: fail\n",
            encoding="utf-8",
        )
        diags = analyze_path(tmp_path)
        e087 = [d for d in diags if d.code == "MLIP-E087"]
        assert e087

    def test_clean_log_no_e087(self, tmp_path: Path) -> None:
        fixture = tmp_path / "run.log"
        fixture.write_text("All good.\n", encoding="utf-8")
        diags = analyze_path(tmp_path)
        e087 = [d for d in diags if d.code == "MLIP-E087"]
        assert not e087


# ---------------------------------------------------------------------------
# Issue #23: Capability: Code actions
# ---------------------------------------------------------------------------


class TestIssue23CodeActions:
    def test_code_action_add_json_key(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.json"
        content = '{"model":"DPA3.1-3M"}'
        diags = server.compute_diagnostics(uri, content)
        from mlip_lsp.server import _compute_code_actions

        actions = _compute_code_actions(uri, content, diags)
        titles = [a.title for a in actions if hasattr(a, "title")]
        assert any("Add missing key" in t for t in titles)

    def test_code_action_add_import(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.py"
        content = "x = 1\n"
        diags = server.compute_diagnostics(uri, content)
        from mlip_lsp.server import _compute_code_actions

        actions = _compute_code_actions(uri, content, diags)
        titles = [a.title for a in actions if hasattr(a, "title")]
        assert any("Add import" in t for t in titles)

    def test_code_action_add_symbol(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.py"
        content = "from ase import Atoms\natoms = Atoms()\n"
        diags = server.compute_diagnostics(uri, content)
        from mlip_lsp.server import _compute_code_actions

        actions = _compute_code_actions(uri, content, diags)
        titles = [a.title for a in actions if hasattr(a, "title")]
        assert any("Add symbol" in t for t in titles)

    def test_code_action_yaml_add_key(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.yaml"
        content = "model: DPA3.1-3M\n"
        diags = server.compute_diagnostics(uri, content)
        from mlip_lsp.server import _compute_code_actions

        actions = _compute_code_actions(uri, content, diags)
        titles = [a.title for a in actions if hasattr(a, "title")]
        assert any("Add missing key" in t for t in titles)

    def test_code_action_has_workspace_edit(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.json"
        content = '{"model":"DPA3.1-3M"}'
        diags = server.compute_diagnostics(uri, content)
        from mlip_lsp.server import _compute_code_actions

        actions = _compute_code_actions(uri, content, diags)
        for action in actions:
            if hasattr(action, "edit") and action.edit is not None:
                assert action.edit.document_changes is not None
                break
        else:
            # At least some actions should have edits
            actions_with_edits = [a for a in actions if hasattr(a, "edit") and a.edit is not None]
            assert actions_with_edits


# ---------------------------------------------------------------------------
# Issue #24: Capability: Runtime log parser
# ---------------------------------------------------------------------------


class TestIssue24LogParser:
    def test_log_parser_traceback(self) -> None:
        from mlip_lsp.features.log_parser import log_diagnostics

        content = (
            "Traceback (most recent call last):\n  File 'run.py', line 5\nRuntimeError: fail\n"
        )
        diags = log_diagnostics(content, "run.log")
        assert len(diags) == 1
        assert diags[0].code == "MLIP-E087"

    def test_log_parser_clean(self) -> None:
        from mlip_lsp.features.log_parser import log_diagnostics

        content = "All good.\n"
        diags = log_diagnostics(content, "run.log")
        assert diags == []

    def test_log_via_analyzer(self, tmp_path: Path) -> None:
        fixture = tmp_path / "run.log"
        fixture.write_text(
            "Traceback (most recent call last):\nValueError: bad\n",
            encoding="utf-8",
        )
        diags = analyze_path(tmp_path)
        e087 = [d for d in diags if d.code == "MLIP-E087"]
        assert e087

    def test_log_via_server(self) -> None:
        server = create_server()
        content = "Traceback (most recent call last):\nRuntimeError: fail\n"
        diags = server.compute_diagnostics("file:///tmp/run.log", content)
        e087 = [d for d in diags if d.code == "MLIP-E087"]
        assert e087


# ---------------------------------------------------------------------------
# Rich diagnostics contract (Agent JSON)
# ---------------------------------------------------------------------------


class TestRichDiagnosticsContract:
    def test_mlip_e080_in_rich_payload(self) -> None:
        diag = Diagnostic("MLIP-E080", "error", "JSON parse error", "test.json", 1)
        item = diagnostic_to_dict(diag, software="mlip")
        assert item["code"] == "MLIP-E080"
        assert item["severity"] == "error"
        assert item["category"] == "syntax"

    def test_mlip_e087_in_rich_payload(self) -> None:
        diag = Diagnostic("MLIP-E087", "error", "traceback found", "run.log", 2)
        item = diagnostic_to_dict(diag, software="mlip")
        assert item["code"] == "MLIP-E087"
        assert item["blocking"] is True

    def test_agent_check_payload_structure(self) -> None:
        payload = agent_check_payload(
            software="mlip",
            uri="file:///tmp/test.json",
            diagnostics=[],
        )
        assert payload["diagnostic_engine"] == "1.0"
        assert payload["ok"] is True
        assert payload["software"] == "mlip"
        assert "summary" in payload
