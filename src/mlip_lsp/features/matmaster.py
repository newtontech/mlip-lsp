"""MatMaster execution rules for MLIP workflows.

Encodes the execution contracts that MatMaster expects when
dispatching MLIP jobs. These rules validate that manifests conform
to the structure required for automated execution.
"""

# See also: wiki/concepts/MatMaster_Execution_Contract.md, wiki/entities/MLIP_Manifest.md

from __future__ import annotations

from typing import Any

from ..diagnostics import Diagnostic

# Known MLIP model families and their execution requirements
MODEL_FAMILIES: dict[str, dict[str, Any]] = {
    "DPA3.1-3M": {"engine": "dp", "requires_model_file": True},
    "DPA2": {"engine": "dp", "requires_model_file": True},
    "MACE": {"engine": "mace", "requires_model_file": True},
    "NEP": {"engine": "gpumd", "requires_model_file": True},
    "CHGNet": {"engine": "chgnet", "requires_model_file": True},
    "M3GNet": {"engine": "m3gnet", "requires_model_file": True},
    "SevenNet": {"engine": "sevenn", "requires_model_file": True},
    "ORB": {"engine": "orb", "requires_model_file": True},
}

# Valid structure file extensions
STRUCTURE_EXTENSIONS = {".cif", ".xyz", ".poscar", ".contcar", ".json", ".yaml", ".yml"}

# Valid task types and their required parameters
TASK_REQUIREMENTS: dict[str, list[str]] = {
    "optimize": [],
    "md": ["temperature", "steps"],
    "static": [],
    "relax": [],
    "phonon": [],
    "neb": [],
    "transition_state": [],
}

# Supported file extensions for manifests
MANIFEST_EXTENSIONS = {".json", ".yaml", ".yml"}


def validate_manifest_structure(manifest: dict[str, Any], file_path: str) -> list[Diagnostic]:
    """Validate a parsed manifest against MatMaster execution contracts."""
    diagnostics: list[Diagnostic] = []

    # Check required keys with MLIP-prefixed codes
    key_to_code = {
        "model": "MLIP-E082",
        "task": "MLIP-E083",
        "structure": "MLIP-E084",
    }
    for key, code in key_to_code.items():
        if key not in manifest:
            diagnostics.append(
                Diagnostic(
                    code=code,
                    severity="error",
                    message=f"manifest is missing required key '{key}'",
                    file=file_path,
                    line=1,
                    suggested_fix={"kind": "add_json_key", "key": key},
                    confidence=0.9,
                )
            )

    # Validate model value against known families
    model = manifest.get("model")
    if model is not None and isinstance(model, str):
        if model not in MODEL_FAMILIES:
            diagnostics.append(
                Diagnostic(
                    code="MLIP-E082",
                    severity="warning",
                    message=(
                        f"unknown MLIP model '{model}'; known models: "
                        f"{', '.join(sorted(MODEL_FAMILIES))}"
                    ),
                    file=file_path,
                    line=1,
                    suggested_fix={"kind": "check_model_name", "model": model},
                    confidence=0.7,
                )
            )

    # Validate task value
    task = manifest.get("task")
    if task is not None and isinstance(task, str):
        if task not in TASK_REQUIREMENTS:
            diagnostics.append(
                Diagnostic(
                    code="MLIP-E083",
                    severity="warning",
                    message=(
                        f"unknown task type '{task}'; valid types: "
                        f"{', '.join(sorted(TASK_REQUIREMENTS))}"
                    ),
                    file=file_path,
                    line=1,
                    suggested_fix={"kind": "check_task_type", "task": task},
                    confidence=0.7,
                )
            )
        else:
            # Check required parameters for the task type
            params = manifest.get("parameters", {})
            if isinstance(params, dict):
                for required_param in TASK_REQUIREMENTS[task]:
                    if required_param not in params:
                        diagnostics.append(
                            Diagnostic(
                                code="MLIP-E083",
                                severity="warning",
                                message=(
                                    f"task '{task}' recommends parameter "
                                    f"'{required_param}' which is not set"
                                ),
                                file=file_path,
                                line=1,
                                suggested_fix={
                                    "kind": "add_parameter",
                                    "parameter": required_param,
                                },
                                confidence=0.65,
                            )
                        )

    # Validate structure file extension
    structure = manifest.get("structure")
    if structure is not None and isinstance(structure, str):
        import os

        _, ext = os.path.splitext(structure.lower())
        if ext and ext not in STRUCTURE_EXTENSIONS:
            diagnostics.append(
                Diagnostic(
                    code="MLIP-E084",
                    severity="warning",
                    message=(
                        f"structure file '{structure}' has unsupported extension '{ext}'; "
                        f"expected one of: {', '.join(sorted(STRUCTURE_EXTENSIONS))}"
                    ),
                    file=file_path,
                    line=1,
                    suggested_fix={
                        "kind": "check_structure_extension",
                        "path": structure,
                    },
                    confidence=0.6,
                )
            )

    return diagnostics
