from __future__ import annotations

import json
from pathlib import Path

from mlip_lsp.analyzer import (
    analyze_file,
    analyze_path,
    format_text,
)
from mlip_lsp.diagnostics import Diagnostic

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# JSON manifest tests
# ---------------------------------------------------------------------------


class TestJSONManifest:
    def test_valid_manifest_no_errors(self, tmp_path: Path) -> None:
        fixture = tmp_path / "mlip_submit.json"
        fixture.write_text(
            json.dumps({"model": "DPA3.1-3M", "structure": "input.cif", "task": "optimize"}),
            encoding="utf-8",
        )
        diagnostics = analyze_path(tmp_path)
        errors = [d for d in diagnostics if d.severity == "error"]
        assert not errors

    def test_valid_manifest_with_params_no_errors(self, tmp_path: Path) -> None:
        fixture = tmp_path / "submit.json"
        fixture.write_text(
            json.dumps(
                {
                    "model": "MACE",
                    "structure": "POSCAR",
                    "task": "md",
                    "parameters": {"temperature": 300, "steps": 10000},
                }
            ),
            encoding="utf-8",
        )
        diagnostics = analyze_path(tmp_path)
        errors = [d for d in diagnostics if d.severity == "error"]
        assert not errors

    def test_missing_model_key(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.json"
        fixture.write_text(
            json.dumps({"structure": "input.cif", "task": "optimize"}),
            encoding="utf-8",
        )
        diagnostics = analyze_path(tmp_path)
        codes = [d.code for d in diagnostics]
        assert "MLIP101" in codes

    def test_missing_structure_key(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.json"
        fixture.write_text(
            json.dumps({"model": "DPA3.1-3M", "task": "static"}),
            encoding="utf-8",
        )
        diagnostics = analyze_path(tmp_path)
        codes = [d.code for d in diagnostics]
        assert "MLIP101" in codes

    def test_missing_task_key(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.json"
        fixture.write_text(
            json.dumps({"model": "DPA3.1-3M", "structure": "input.cif"}),
            encoding="utf-8",
        )
        diagnostics = analyze_path(tmp_path)
        codes = [d.code for d in diagnostics]
        assert "MLIP101" in codes

    def test_missing_multiple_keys(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.json"
        fixture.write_text('{"model":"DPA3.1-3M"}', encoding="utf-8")
        diagnostics = analyze_path(tmp_path)
        missing_warnings = [d for d in diagnostics if d.code == "MLIP101"]
        assert len(missing_warnings) == 2  # structure + task

    def test_invalid_json_reports_error(self, tmp_path: Path) -> None:
        fixture = tmp_path / "broken.json"
        fixture.write_text('{"model": "broken" trailing}', encoding="utf-8")
        diagnostics = analyze_path(tmp_path)
        errors = [d for d in diagnostics if d.severity == "error"]
        assert errors
        assert errors[0].code == "MLIP001"

    def test_empty_json_object_reports_missing_keys(self, tmp_path: Path) -> None:
        fixture = tmp_path / "empty.json"
        fixture.write_text("{}", encoding="utf-8")
        diagnostics = analyze_path(tmp_path)
        missing = [d for d in diagnostics if d.code == "MLIP101"]
        assert len(missing) == 3  # model, structure, task

    def test_json_array_no_crash(self, tmp_path: Path) -> None:
        fixture = tmp_path / "array.json"
        fixture.write_text("[1, 2, 3]", encoding="utf-8")
        diagnostics = analyze_path(tmp_path)
        # Should not crash; array is valid JSON but not a manifest dict
        assert isinstance(diagnostics, list)

    def test_manifest_has_suggested_fix(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.json"
        fixture.write_text('{"model":"DPA3.1-3M"}', encoding="utf-8")
        diagnostics = analyze_path(tmp_path)
        for d in diagnostics:
            if d.code == "MLIP101":
                assert d.suggested_fix is not None
                assert "key" in d.suggested_fix


class TestFixtureFiles:
    """Tests using the static fixture files in tests/fixtures/."""

    def test_valid_manifest_fixture(self) -> None:
        diagnostics = analyze_file(FIXTURES / "valid_manifest.json")
        errors = [d for d in diagnostics if d.severity == "error"]
        assert not errors

    def test_manifest_with_params_fixture(self) -> None:
        diagnostics = analyze_file(FIXTURES / "manifest_with_params.json")
        errors = [d for d in diagnostics if d.severity == "error"]
        assert not errors

    def test_missing_structure_fixture(self) -> None:
        diagnostics = analyze_file(FIXTURES / "missing_structure.json")
        codes = [d.code for d in diagnostics]
        assert "MLIP101" in codes

    def test_missing_model_fixture(self) -> None:
        diagnostics = analyze_file(FIXTURES / "missing_model.json")
        codes = [d.code for d in diagnostics]
        assert "MLIP101" in codes

    def test_missing_task_fixture(self) -> None:
        diagnostics = analyze_file(FIXTURES / "missing_task.json")
        codes = [d.code for d in diagnostics]
        assert "MLIP101" in codes

    def test_invalid_json_fixture(self) -> None:
        diagnostics = analyze_file(FIXTURES / "invalid_json.json")
        errors = [d for d in diagnostics if d.severity == "error"]
        assert errors
        assert errors[0].code == "MLIP001"


# ---------------------------------------------------------------------------
# Python script tests
# ---------------------------------------------------------------------------


class TestPythonScripts:
    def test_valid_ase_script_no_errors(self, tmp_path: Path) -> None:
        fixture = tmp_path / "run.py"
        fixture.write_text(
            "from ase import Atoms\n"
            "from ase.optimize import BFGS\n"
            "\n"
            'structure = Atoms("H2", positions=[[0,0,0],[0,0,0.74]])\n'
            "calc = None\n"
            "structure.calc = calc\n",
            encoding="utf-8",
        )
        diagnostics = analyze_path(tmp_path)
        errors = [d for d in diagnostics if d.severity == "error"]
        assert not errors

    def test_syntax_error_in_script(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.py"
        fixture.write_text("x = \n", encoding="utf-8")
        diagnostics = analyze_path(tmp_path)
        errors = [d for d in diagnostics if d.severity == "error"]
        assert errors

    def test_missing_ase_import_warning(self, tmp_path: Path) -> None:
        fixture = tmp_path / "no_ase.py"
        fixture.write_text(
            "structure = [1, 2, 3]\nprint(structure)\n",
            encoding="utf-8",
        )
        diagnostics = analyze_path(tmp_path)
        codes = [d.code for d in diagnostics]
        assert "MLIP101" in codes

    def test_missing_structure_symbol_warning(self, tmp_path: Path) -> None:
        fixture = tmp_path / "no_structure.py"
        fixture.write_text(
            "from ase import Atoms\natoms = Atoms('Cu')\nprint(atoms)\n",
            encoding="utf-8",
        )
        diagnostics = analyze_path(tmp_path)
        codes = [d.code for d in diagnostics]
        assert "MLIP102" in codes

    def test_valid_ase_script_fixture(self) -> None:
        diagnostics = analyze_file(FIXTURES / "valid_ase_script.py")
        errors = [d for d in diagnostics if d.severity == "error"]
        assert not errors

    def test_syntax_error_script_fixture(self) -> None:
        diagnostics = analyze_file(FIXTURES / "syntax_error_script.py")
        errors = [d for d in diagnostics if d.severity == "error"]
        assert errors
        assert errors[0].code == "MLIP001"


# ---------------------------------------------------------------------------
# Formatter tests
# ---------------------------------------------------------------------------


class TestFormatter:
    def test_idempotent_on_json(self) -> None:
        text = '{"model":"DPA3.1-3M","structure":"input.cif","task":"optimize"}\n'
        assert format_text(format_text(text)) == format_text(text)

    def test_key_value_alignment(self) -> None:
        text = "cutoff = 5.0\nlambda_1 = 0.1\n"
        result = format_text(text)
        lines = result.strip().split("\n")
        assert len(lines) == 2
        # Both lines should have '=' aligned
        eq_positions = [line.index("=") for line in lines]
        assert eq_positions[0] == eq_positions[1]

    def test_preserves_comments(self) -> None:
        text = "# This is a comment\ncutoff = 5.0\n"
        result = format_text(text)
        assert "# This is a comment" in result

    def test_blank_line_preservation(self) -> None:
        text = "cutoff = 5.0\n\nlambda_1 = 0.1\n"
        result = format_text(text)
        assert "\n\n" in result

    def test_keyword_spacing(self) -> None:
        text = "generation  200000\npopulation   50\n"
        result = format_text(text)
        lines = result.strip().split("\n")
        assert len(lines) == 2

    def test_trailing_newline(self) -> None:
        text = "cutoff = 5.0"
        result = format_text(text)
        assert result.endswith("\n")

    def test_empty_input(self) -> None:
        result = format_text("")
        assert result == "\n"

    def test_comment_only(self) -> None:
        text = "# just a comment\n"
        result = format_text(text)
        assert result == text

    def test_nep_config_formatting(self) -> None:
        text = "# NEP config\ngeneration=200000\npopulation = 50\ncutoff= 5.0\n"
        result = format_text(text)
        for line in result.strip().split("\n"):
            if "=" in line:
                key, val = line.split("=", 1)
                assert key.strip() in ("generation", "population", "cutoff")


# ---------------------------------------------------------------------------
# Path / directory handling tests
# ---------------------------------------------------------------------------


class TestPathHandling:
    def test_empty_directory_reports_error(self, tmp_path: Path) -> None:
        diagnostics = analyze_path(tmp_path)
        assert diagnostics
        assert diagnostics[0].code == "MLIP201"

    def test_single_file(self, tmp_path: Path) -> None:
        fixture = tmp_path / "test.json"
        fixture.write_text(
            json.dumps({"model": "DPA3.1-3M", "structure": "input.cif", "task": "optimize"}),
            encoding="utf-8",
        )
        diagnostics = analyze_path(tmp_path / "test.json")
        assert isinstance(diagnostics, list)

    def test_nested_directories(self, tmp_path: Path) -> None:
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        fixture = subdir / "manifest.json"
        fixture.write_text(
            json.dumps({"model": "DPA3.1-3M", "structure": "input.cif", "task": "optimize"}),
            encoding="utf-8",
        )
        diagnostics = analyze_path(tmp_path)
        errors = [d for d in diagnostics if d.severity == "error"]
        assert not errors

    def test_unsupported_file_ignored(self, tmp_path: Path) -> None:
        fixture = tmp_path / "readme.txt"
        fixture.write_text("This is a readme", encoding="utf-8")
        diagnostics = analyze_path(tmp_path)
        assert diagnostics
        assert diagnostics[0].code == "MLIP201"

    def test_non_utf8_file(self, tmp_path: Path) -> None:
        fixture = tmp_path / "binary.json"
        fixture.write_bytes(b"\x80\x81\x82")
        diagnostics = analyze_path(tmp_path)
        # The file won't be picked up as valid JSON anyway, or will error
        assert isinstance(diagnostics, list)

    def test_multiple_files_sorted(self, tmp_path: Path) -> None:
        for name, content in [
            ("a.json", json.dumps({"model": "X", "structure": "s", "task": "t"})),
            ("b.py", "from ase import Atoms\nstructure = Atoms()\n"),
        ]:
            (tmp_path / name).write_text(content, encoding="utf-8")
        diagnostics = analyze_path(tmp_path)
        files = [d.file for d in diagnostics]
        assert files == sorted(files)

    def test_unsupported_single_file_reports_no_files(self, tmp_path: Path) -> None:
        fixture = tmp_path / "data.csv"
        fixture.write_text("a,b,c\n1,2,3", encoding="utf-8")
        diagnostics = analyze_path(fixture)
        assert diagnostics
        assert diagnostics[0].code == "MLIP201"


# ---------------------------------------------------------------------------
# Diagnostic data class tests
# ---------------------------------------------------------------------------


class TestDiagnostic:
    def test_to_json(self) -> None:
        d = Diagnostic("MLIP001", "error", "test message", "file.json", 1)
        j = d.to_json()
        assert j["code"] == "MLIP001"
        assert j["severity"] == "error"
        assert j["message"] == "test message"
        assert j["file"] == "file.json"
        assert j["line"] == 1
        assert j["column"] == 1
        assert j["evidence"] == []
        assert j["suggested_fix"] is None
        assert j["confidence"] == 1.0

    def test_frozen(self) -> None:
        d = Diagnostic("MLIP001", "error", "test", "f", 1)
        import pytest

        with pytest.raises(AttributeError):
            d.code = "changed"  # type: ignore[misc]

    def test_all_fields(self) -> None:
        d = Diagnostic(
            "MLIP101",
            "warning",
            "missing key",
            "manifest.json",
            1,
            column=5,
            evidence=["key 'model' not found"],
            suggested_fix={"kind": "add_json_key", "key": "model"},
            confidence=0.78,
        )
        j = d.to_json()
        assert j["column"] == 5
        assert len(j["evidence"]) == 1
        assert j["suggested_fix"]["key"] == "model"
        assert j["confidence"] == 0.78
