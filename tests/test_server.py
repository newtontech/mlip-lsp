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
        # pygls server should be accessible
        assert hasattr(server, "lsp") or hasattr(server, "server")


class TestDiagnostics:
    def test_publish_diagnostics_for_json(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.json"
        content = '{"model":"X"}'
        diags = server.compute_diagnostics(uri, content)
        assert len(diags) > 0
        # Should report missing structure and task keys
        codes = [d.code for d in diags]
        assert "MLIP101" in codes

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


class TestCompletion:
    def test_json_key_completion(self) -> None:
        server = create_server()
        uri = "file:///tmp/test.json"
        content = '{"model":"DPA3.1-3M",'
        # Trigger completion at position after the comma
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
