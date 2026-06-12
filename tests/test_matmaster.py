"""Tests for MatMaster execution rules (Issue #8)."""

from __future__ import annotations

from mlip_lsp.features.matmaster import (
    MANIFEST_EXTENSIONS,
    MODEL_FAMILIES,
    STRUCTURE_EXTENSIONS,
    TASK_REQUIREMENTS,
    validate_manifest_structure,
)


class TestModelFamilies:
    def test_known_models_defined(self) -> None:
        expected = {"DPA3.1-3M", "DPA2", "MACE", "NEP", "CHGNet", "M3GNet", "SevenNet", "ORB"}
        assert set(MODEL_FAMILIES.keys()) == expected

    def test_each_model_has_engine(self) -> None:
        for model, info in MODEL_FAMILIES.items():
            assert "engine" in info
            assert info["engine"]

    def test_each_model_has_requires_model_file(self) -> None:
        for model, info in MODEL_FAMILIES.items():
            assert "requires_model_file" in info


class TestTaskRequirements:
    def test_known_tasks_defined(self) -> None:
        expected = {"optimize", "md", "static", "relax", "phonon", "neb", "transition_state"}
        assert set(TASK_REQUIREMENTS.keys()) == expected

    def test_md_requires_temperature_and_steps(self) -> None:
        assert "temperature" in TASK_REQUIREMENTS["md"]
        assert "steps" in TASK_REQUIREMENTS["md"]


class TestValidateManifest:
    def test_valid_manifest_no_diagnostics(self) -> None:
        manifest = {"model": "DPA3.1-3M", "structure": "input.cif", "task": "optimize"}
        diags = validate_manifest_structure(manifest, "test.json")
        assert diags == []

    def test_missing_model_e082(self) -> None:
        manifest = {"structure": "input.cif", "task": "optimize"}
        diags = validate_manifest_structure(manifest, "test.json")
        codes = [d.code for d in diags]
        assert "MLIP-E082" in codes

    def test_missing_task_e083(self) -> None:
        manifest = {"model": "DPA3.1-3M", "structure": "input.cif"}
        diags = validate_manifest_structure(manifest, "test.json")
        codes = [d.code for d in diags]
        assert "MLIP-E083" in codes

    def test_missing_structure_e084(self) -> None:
        manifest = {"model": "DPA3.1-3M", "task": "optimize"}
        diags = validate_manifest_structure(manifest, "test.json")
        codes = [d.code for d in diags]
        assert "MLIP-E084" in codes

    def test_unknown_model_warning(self) -> None:
        manifest = {"model": "UnknownModel", "structure": "input.cif", "task": "optimize"}
        diags = validate_manifest_structure(manifest, "test.json")
        model_warnings = [d for d in diags if "unknown MLIP model" in d.message]
        assert model_warnings

    def test_unknown_task_warning(self) -> None:
        manifest = {"model": "DPA3.1-3M", "structure": "input.cif", "task": "fly"}
        diags = validate_manifest_structure(manifest, "test.json")
        task_warnings = [d for d in diags if "unknown task type" in d.message]
        assert task_warnings

    def test_md_missing_parameters(self) -> None:
        manifest = {"model": "MACE", "structure": "POSCAR", "task": "md"}
        diags = validate_manifest_structure(manifest, "test.json")
        param_warnings = [d for d in diags if "recommends parameter" in d.message]
        assert len(param_warnings) == 2  # temperature + steps

    def test_md_with_parameters_no_warning(self) -> None:
        manifest = {
            "model": "MACE",
            "structure": "POSCAR",
            "task": "md",
            "parameters": {"temperature": 300, "steps": 10000},
        }
        diags = validate_manifest_structure(manifest, "test.json")
        param_warnings = [d for d in diags if "recommends parameter" in d.message]
        assert param_warnings == []

    def test_unsupported_structure_extension(self) -> None:
        manifest = {"model": "DPA3.1-3M", "structure": "input.dat", "task": "optimize"}
        diags = validate_manifest_structure(manifest, "test.json")
        ext_warnings = [d for d in diags if "unsupported extension" in d.message]
        assert ext_warnings

    def test_suggested_fix_present(self) -> None:
        manifest = {"structure": "s", "task": "t"}
        diags = validate_manifest_structure(manifest, "test.json")
        for d in diags:
            assert d.suggested_fix is not None
            assert "kind" in d.suggested_fix

    def test_manifest_extensions(self) -> None:
        assert ".json" in MANIFEST_EXTENSIONS
        assert ".yaml" in MANIFEST_EXTENSIONS
        assert ".yml" in MANIFEST_EXTENSIONS

    def test_structure_extensions(self) -> None:
        assert ".cif" in STRUCTURE_EXTENSIONS
        assert ".xyz" in STRUCTURE_EXTENSIONS
        assert ".poscar" in STRUCTURE_EXTENSIONS
