from __future__ import annotations

import json
from pathlib import Path

import pytest

from mlip_lsp.cli import fmt_main, lint_main, lsp_main
from mlip_lsp.cli import test_main as run_test_main


class TestLintCLI:
    def test_lint_valid_json(self, tmp_path: Path) -> None:
        fixture = tmp_path / "good.json"
        fixture.write_text(
            json.dumps({"model": "DPA3.1-3M", "structure": "input.cif", "task": "optimize"}),
            encoding="utf-8",
        )
        rc = lint_main([str(fixture)])
        assert rc == 0

    def test_lint_invalid_json_returns_1(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.json"
        fixture.write_text('{"model":}', encoding="utf-8")
        rc = lint_main([str(fixture)])
        assert rc == 1

    def test_lint_json_output(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        fixture = tmp_path / "bad.json"
        fixture.write_text('{"model":"X"}', encoding="utf-8")
        lint_main([str(fixture), "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert any(d["code"] in ("MLIP-E082", "MLIP-E083", "MLIP-E084") for d in data)

    def test_lint_empty_dir(self, tmp_path: Path) -> None:
        rc = lint_main([str(tmp_path)])
        assert rc == 1  # error: no supported files

    def test_lint_text_output(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        fixture = tmp_path / "bad.json"
        fixture.write_text('{"model":}', encoding="utf-8")
        lint_main([str(fixture)])
        captured = capsys.readouterr()
        assert "error" in captured.out
        assert "MLIP-E080" in captured.out

    def test_lint_yaml_valid(self, tmp_path: Path) -> None:
        fixture = tmp_path / "good.yaml"
        fixture.write_text(
            "model: DPA3.1-3M\nstructure: input.cif\ntask: optimize\n",
            encoding="utf-8",
        )
        rc = lint_main([str(fixture)])
        assert rc == 0

    def test_lint_yaml_invalid(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.yaml"
        fixture.write_text(
            "model: DPA3.1-3M\n  bad_indent: true\n",
            encoding="utf-8",
        )
        rc = lint_main([str(fixture)])
        assert rc == 1


class TestFmtCLI:
    def test_fmt_stdout(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        fixture = tmp_path / "test.txt"
        fixture.write_text("cutoff = 5.0\n", encoding="utf-8")
        rc = fmt_main([str(fixture)])
        assert rc == 0
        output = capsys.readouterr().out
        assert "cutoff" in output

    def test_fmt_write_in_place(self, tmp_path: Path) -> None:
        fixture = tmp_path / "test.txt"
        fixture.write_text("cutoff=5.0\nlambda_1=0.1\n", encoding="utf-8")
        rc = fmt_main(["-w", str(fixture)])
        assert rc == 0
        content = fixture.read_text(encoding="utf-8")
        assert "cutoff" in content

    def test_fmt_multiple_files(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("x = 1\n", encoding="utf-8")
        f2.write_text("y = 2\n", encoding="utf-8")
        rc = fmt_main([str(f1), str(f2)])
        assert rc == 0


class TestLspCLI:
    def test_lsp_stdio_flag(self) -> None:
        with pytest.raises(SystemExit):
            lsp_main([])

    def test_lsp_server_creates_successfully(self) -> None:
        from mlip_lsp.server import create_server

        server = create_server()
        assert server is not None
        assert hasattr(server, "server")


class TestTestCLI:
    def test_static_lint(self, tmp_path: Path) -> None:
        fixture = tmp_path / "good.json"
        fixture.write_text(
            json.dumps({"model": "DPA3.1-3M", "structure": "input.cif", "task": "optimize"}),
            encoding="utf-8",
        )
        rc = run_test_main(["static", str(fixture)])
        assert rc == 0

    def test_static_lint_json(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        fixture = tmp_path / "bad.json"
        fixture.write_text('{"model":"X"}', encoding="utf-8")
        run_test_main(["static", str(fixture), "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
