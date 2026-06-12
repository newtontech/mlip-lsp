"""Tests for the LSP server (pygls-based)."""

from __future__ import annotations

import json

from mlip_lsp.server import create_server


class TestServerCreation:
    def test_create_server_returns_server(self) -> None:
        server = create_server()
        assert server is not None

    def test_server_has_lsp_attribute(self) -> None:
        server = create_server()
        assert hasattr(server, "lsp") or hasattr(server, "server")


class TestDiagnostics:
    def test_publish_diagnostics_for_json(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.json"
        content = '{"model":"X"}'
        diags = server.compute_diagnostics(uri, content)
        assert len(diags) > 0
        codes = [d.code for d in diags]
        assert "MLIP-E083" in codes  # missing task
        assert "MLIP-E084" in codes  # missing structure

    def test_publish_diagnostics_for_valid_json(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.json"
        content = json.dumps({"model": "DPA3.1-3M", "structure": "input.cif", "task": "optimize"})
        diags = server.compute_diagnostics(uri, content)
        errors = [d for d in diags if d.severity == "error"]
        assert not errors

    def test_publish_diagnostics_for_python(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.py"
        content = "from ase import Atoms\nstructure = Atoms()\n"
        diags = server.compute_diagnostics(uri, content)
        errors = [d for d in diags if d.severity == "error"]
        assert not errors

    def test_publish_diagnostics_for_syntax_error(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.py"
        content = "x = \n"
        diags = server.compute_diagnostics(uri, content)
        errors = [d for d in diags if d.severity == "error"]
        assert errors
        assert errors[0].code == "MLIP-E080"

    def test_diagnostics_invalid_json_e080(self) -> None:
        """MLIP-E080: invalid JSON."""
        server = create_server()
        uri = "file:///tmp/bad.json"
        content = '{"model": broken}'
        diags = server.compute_diagnostics(uri, content)
        errors = [d for d in diags if d.severity == "error"]
        assert errors
        assert errors[0].code == "MLIP-E080"

    def test_diagnostics_invalid_yaml_e081(self) -> None:
        """MLIP-E081: invalid YAML."""
        server = create_server()
        uri = "file:///tmp/bad.yaml"
        content = "model: DPA3.1-3M\n  bad_indent: true\n"
        diags = server.compute_diagnostics(uri, content)
        errors = [d for d in diags if d.severity == "error"]
        assert errors
        assert errors[0].code == "MLIP-E081"

    def test_diagnostics_missing_model_e082(self) -> None:
        """MLIP-E082: missing model key."""
        server = create_server()
        uri = "file:///tmp/test.json"
        content = json.dumps({"structure": "s", "task": "t"})
        diags = server.compute_diagnostics(uri, content)
        codes = [d.code for d in diags]
        assert "MLIP-E082" in codes

    def test_diagnostics_missing_task_e083(self) -> None:
        """MLIP-E083: missing task key."""
        server = create_server()
        uri = "file:///tmp/test.json"
        content = json.dumps({"model": "m", "structure": "s"})
        diags = server.compute_diagnostics(uri, content)
        codes = [d.code for d in diags]
        assert "MLIP-E083" in codes

    def test_diagnostics_missing_structure_e084(self) -> None:
        """MLIP-E084: missing structure key."""
        server = create_server()
        uri = "file:///tmp/test.json"
        content = json.dumps({"model": "m", "task": "t"})
        diags = server.compute_diagnostics(uri, content)
        codes = [d.code for d in diags]
        assert "MLIP-E084" in codes

    def test_diagnostics_missing_ase_w080(self) -> None:
        """MLIP-W080: missing ASE import."""
        server = create_server()
        uri = "file:///tmp/test.py"
        content = "structure = [1, 2, 3]\n"
        diags = server.compute_diagnostics(uri, content)
        codes = [d.code for d in diags]
        assert "MLIP-W080" in codes

    def test_diagnostics_missing_structure_symbol_e085(self) -> None:
        """MLIP-E085: missing structure symbol."""
        server = create_server()
        uri = "file:///tmp/test.py"
        content = "from ase import Atoms\natoms = Atoms('Cu')\n"
        diags = server.compute_diagnostics(uri, content)
        codes = [d.code for d in diags]
        assert "MLIP-E085" in codes

    def test_diagnostics_log_traceback_e087(self) -> None:
        """MLIP-E087: log file with traceback."""
        server = create_server()
        uri = "file:///tmp/mlip.log"
        content = (
            "Starting...\n"
            "Traceback (most recent call last):\n"
            '  File "run.py", line 5\n'
            "RuntimeError: bad\n"
        )
        diags = server.compute_diagnostics(uri, content)
        codes = [d.code for d in diags]
        assert "MLIP-E087" in codes

    def test_diagnostics_yaml_missing_model_e082(self) -> None:
        """MLIP-E082 in YAML: missing model key."""
        server = create_server()
        uri = "file:///tmp/test.yaml"
        content = "structure: s\ntask: t\n"
        diags = server.compute_diagnostics(uri, content)
        codes = [d.code for d in diags]
        assert "MLIP-E082" in codes


class TestCompletion:
    def test_json_key_completion(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.json"
        content = '{"model":"DPA3.1-3M",'
        items = server.complete(uri, content, line=0, character=22)
        assert len(items) > 0
        labels = [item["label"] for item in items]
        assert any("structure" in label for label in labels)

    def test_python_import_completion(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.py"
        content = "from "
        items = server.complete(uri, content, line=0, character=5)
        assert len(items) > 0

    def test_yaml_key_completion(self) -> None:
        """YAML completion: suggest keys at empty line after colon."""
        server = create_server()
        uri = "file:///tmp/test.yaml"
        content = "model: DPA3.1-3M\n"
        items = server.complete(uri, content, line=1, character=0)
        assert len(items) > 0
        labels = [item["label"] for item in items]
        assert any("structure" in label for label in labels)


class TestHover:
    def test_hover_json_key(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.json"
        content = '{"model":"DPA3.1-3M","structure":"input.cif","task":"optimize"}'
        result = server.hover(uri, content, line=0, character=2)
        assert result is not None
        assert "model" in result.lower() or "mlip" in result.lower()

    def test_hover_python_keyword(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.py"
        content = "from ase import Atoms\n"
        result = server.hover(uri, content, line=0, character=5)
        assert result is not None

    def test_hover_yaml_key(self) -> None:
        """Hover over YAML key shows documentation."""
        server = create_server()
        uri = "file:///tmp/test.yaml"
        content = "model: DPA3.1-3M\nstructure: input.cif\ntask: optimize\n"
        result = server.hover(uri, content, line=0, character=2)
        assert result is not None
        assert "model" in result.lower() or "MLIP" in result

    def test_hover_python_atoms(self) -> None:
        """Hover over Atoms symbol."""
        server = create_server()
        uri = "file:///tmp/test.py"
        content = "from ase import Atoms\n"
        result = server.hover(uri, content, line=0, character=18)
        assert result is not None
        assert "Atoms" in result


class TestFormatting:
    def test_format_document(self) -> None:
        server = create_server()
        content = "cutoff=5.0\nlambda_1=0.1\n"
        result = server.format(content)
        assert result != content
        assert "cutoff" in result

    def test_format_preserves_comments(self) -> None:
        server = create_server()
        content = "# comment\ncutoff=5.0\n"
        result = server.format(content)
        assert "# comment" in result
