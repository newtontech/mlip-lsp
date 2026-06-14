"""Universal generated-input preflight capabilities.

This module implements the four fleet-wide preflight capabilities called out in
``newtontech/mlip-lsp#31`` against a *generic artifact-role model*, so the
checks generalize to any backend in the scientific LSP fleet instead of being
wired to MatMaster submission policy:

* ``version-aware-keywords``  - explicit runtime/version assumption metadata and
  model-family/engine compatibility validation derived from the builtin
  ``MODEL_FAMILIES`` registry, never guessed.
* ``cross-artifact-graph``   - resolves the case as a graph of artifacts with
  stable roles (primary-input, model-potential, structure, task-parameters,
  training-config). Cross-file checks operate on the graph rather than ad-hoc
  manifest keys, so the same model works for any fleet backend.
* ``code-actions``           - normalizes repair hints/actions on every
  diagnostic and exposes a blocking gate the agent CLI can run as
  ``check --fail-on-blocking``.
* ``fleet-regression-fixtures`` - ``fleet_manifest`` returns a machine-readable
  description of the preflight surface (codes, capabilities, fixture
  expectations) so the parent ``bohrium_skills`` probe/report workflow can
  consume regression evidence without re-deriving it.

The diagnostics emitted here are plain dictionaries (not the legacy
``Diagnostic`` dataclass) so they can carry the richer ``DiagnosticEnvelope/v1``
fields (``source_provenance``, ``domain_tags``, ``facts``, ``artifact_roles``,
``version_assumption``, ``actions``) directly.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .features.matmaster import (
    MANIFEST_EXTENSIONS,
    MODEL_FAMILIES,
    STRUCTURE_EXTENSIONS,
    TASK_REQUIREMENTS,
)
from .rich_diagnostics import DIAGNOSTIC_ENVELOPE_VERSION

# --- Artifact-role model ---------------------------------------------------

# Generic roles. These are intentionally software-agnostic: every fleet backend
# can map its native artifacts onto this same small role set, which is what lets
# the parent router consume cross-file checks without learning MatMaster
# specifics. MLIP's mapping: primary-input is the workflow manifest, the trained
# potential/weights file is model-potential, the input structure is structure,
# the task's parameter block is task-parameters, and an optional referenced
# training config is training-config.
ROLE_PRIMARY_INPUT = "primary-input"
ROLE_MODEL_POTENTIAL = "model-potential"
ROLE_STRUCTURE = "structure"
ROLE_TASK_PARAMETERS = "task-parameters"
ROLE_TRAINING_CONFIG = "training-config"

ALL_ROLES = (
    ROLE_PRIMARY_INPUT,
    ROLE_MODEL_POTENTIAL,
    ROLE_STRUCTURE,
    ROLE_TASK_PARAMETERS,
    ROLE_TRAINING_CONFIG,
)

# Codes reserved for the universal preflight surface. They use the ``MLIP6xx``
# band so they sort after existing rule codes and stay identifiable as
# cross-fleet preflight findings.
CODE_MISSING_ARTIFACT = "MLIP601"
CODE_MODEL_FAMILY_MISMATCH = "MLIP602"
CODE_TASK_PARAM_MISMATCH = "MLIP603"
CODE_UNRESOLVED_ARTIFACT = "MLIP604"
CODE_MISSING_REQUIRED_KEY = "MLIP605"
CODE_UNSUPPORTED_STRUCTURE_EXT = "MLIP606"
CODE_SUSPICIOUS_TASK_PARAMS = "MLIP607"
CODE_VERSION_ASSUMPTION = "MLIP608"
CODE_MODEL_ENGINE_INCOMPATIBLE = "MLIP609"


@dataclass(frozen=True)
class ArtifactNode:
    """A node in the cross-artifact graph.

    ``role`` is one of the fleet-generic roles above; ``path`` is the resolved
    filesystem path (may be a non-existent reference, which is itself a
    finding); ``source`` records where the reference originated so consumers
    can trace provenance.
    """

    role: str
    path: Path
    exists: bool
    source: str
    referenced_from: tuple[str, int] | None = None
    detail: dict[str, Any] | None = None


@dataclass
class ArtifactGraph:
    """Generic cross-artifact graph built from a parsed case directory."""

    case_dir: Path
    nodes: list[ArtifactNode] = field(default_factory=list)

    def by_role(self, role: str) -> list[ArtifactNode]:
        return [node for node in self.nodes if node.role == role]

    def to_json(self) -> list[dict[str, Any]]:
        """Serialize the graph for the parent probe/report workflow."""

        def _node_json(node: ArtifactNode) -> dict[str, Any]:
            payload: dict[str, Any] = {
                "role": node.role,
                "path": str(node.path),
                "exists": node.exists,
                "source": node.source,
            }
            if node.referenced_from is not None:
                payload["referenced_from"] = {
                    "path": node.referenced_from[0],
                    "line": node.referenced_from[1],
                }
            if node.detail:
                payload["detail"] = node.detail
            return payload

        return sorted(
            (_node_json(node) for node in self.nodes),
            key=lambda item: (item["role"], item["path"]),
        )


@dataclass(frozen=True)
class ParsedManifest:
    """A parsed MLIP workflow manifest (JSON or YAML)."""

    path: Path
    data: dict[str, Any]
    line_of: dict[str, int] = field(default_factory=dict)
    text: str = ""


def _parse_manifest_at(path: Path) -> ParsedManifest | None:
    """Parse a single manifest file (JSON or YAML) into a ParsedManifest.

    Returns None when the file cannot be parsed as a dict; the legacy analyzer
    already emits the syntax codes (MLIP-E080/MLIP-E081) so preflight does not
    duplicate them.
    """
    text: str
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    suffix = path.suffix.lower()
    data: Any
    if suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None
    elif suffix in (".yaml", ".yml"):
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError:
            return None
    else:
        return None
    if not isinstance(data, dict):
        return None
    return ParsedManifest(path=path, data=data, line_of=_key_lines(text), text=text)


def _key_lines(text: str) -> dict[str, int]:
    """Best-effort 1-based line numbers for top-level manifest keys.

    Used only for ``referenced_from`` provenance; falls back to line 1 when a
    key cannot be located. Works for both JSON (``"key":``) and YAML (``key:``)
    shapes.
    """
    out: dict[str, int] = {}
    for line_no, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith(("#", "//")):
            continue
        key = _leading_key(stripped)
        if key is None:
            continue
        out.setdefault(key, line_no)
    return out


def _leading_key(stripped_line: str) -> str | None:
    if stripped_line.startswith('"'):
        end = stripped_line.find('"', 1)
        if end > 0:
            return stripped_line[1:end]
        return None
    for sep in (":", " ", "\t"):
        idx = stripped_line.find(sep)
        if idx > 0:
            candidate = stripped_line[:idx]
            if candidate and all(ch.isalnum() or ch in "_-." for ch in candidate):
                return candidate
    return None


def find_manifest(case_dir: Path) -> Path | None:
    """Locate the primary workflow manifest in a case directory.

    Prefers files named ``manifest.json``/``manifest.yaml`` then falls back to
    the first supported manifest in the case root. The legacy single-file lint
    path already covers nested files; preflight only needs the root manifest to
    build a meaningful cross-artifact graph.
    """
    for name in ("manifest.json", "manifest.yaml", "manifest.yml"):
        candidate = case_dir / name
        if candidate.is_file():
            return candidate
    for entry in sorted(case_dir.iterdir()):
        if entry.is_file() and entry.suffix.lower() in MANIFEST_EXTENSIONS:
            return entry
    return None


def build_artifact_graph(
    case_dir: Path,
    manifest: ParsedManifest,
) -> ArtifactGraph:
    """Build the cross-artifact graph from a parsed MLIP manifest.

    The model is generic: it records roles + resolved paths + provenance. The
    same shape generalizes to other fleet backends because it never bakes in
    MatMaster/Bohrium runtime concepts (no input_dir, no image, no session).
    """
    case_dir = case_dir.resolve()
    graph = ArtifactGraph(case_dir=case_dir)

    manifest_path = manifest.path.resolve()
    graph.nodes.append(
        ArtifactNode(
            role=ROLE_PRIMARY_INPUT,
            path=manifest_path,
            exists=True,
            source="case-root",
        )
    )

    # structure is always a file reference.
    structure_value = _as_str(manifest.data.get("structure"))
    if structure_value is not None:
        struct_path = (case_dir / structure_value).resolve()
        graph.nodes.append(
            ArtifactNode(
                role=ROLE_STRUCTURE,
                path=struct_path,
                exists=struct_path.exists(),
                source=f"{manifest.path.name}:structure",
                referenced_from=(
                    str(manifest_path),
                    manifest.line_of.get("structure", 1),
                ),
                detail={"declared": structure_value},
            )
        )

    # model can be either a known family name (e.g. DPA3.1-3M) or a path to a
    # trained weights file (recognized by its extension). Only the path form
    # produces a model-potential node.
    model_value = _as_str(manifest.data.get("model"))
    if model_value is not None and _looks_like_file_path(model_value):
        model_path = (case_dir / model_value).resolve()
        graph.nodes.append(
            ArtifactNode(
                role=ROLE_MODEL_POTENTIAL,
                path=model_path,
                exists=model_path.exists(),
                source=f"{manifest.path.name}:model",
                referenced_from=(
                    str(manifest_path),
                    manifest.line_of.get("model", 1),
                ),
                detail={"declared": model_value},
            )
        )

    # training-config is an optional reference (``training``/``config``/
    # ``training_config`` keys). Like model it only forms a node when it points
    # at a file.
    for cfg_key in ("training", "config", "training_config"):
        cfg_value = _as_str(manifest.data.get(cfg_key))
        if cfg_value is not None and _looks_like_file_path(cfg_value):
            cfg_path = (case_dir / cfg_value).resolve()
            graph.nodes.append(
                ArtifactNode(
                    role=ROLE_TRAINING_CONFIG,
                    path=cfg_path,
                    exists=cfg_path.exists(),
                    source=f"{manifest.path.name}:{cfg_key}",
                    referenced_from=(
                        str(manifest_path),
                        manifest.line_of.get(cfg_key, 1),
                    ),
                    detail={"declared": cfg_value, "key": cfg_key},
                )
            )

    # task-parameters is the in-manifest ``parameters`` block for the declared
    # task; it is not a separate file but it is a real artifact role the
    # cross-task checks operate on.
    task_value = _as_str(manifest.data.get("task"))
    params = manifest.data.get("parameters")
    graph.nodes.append(
        ArtifactNode(
            role=ROLE_TASK_PARAMETERS,
            path=manifest_path,
            exists=isinstance(params, dict),
            source=f"{manifest.path.name}:parameters",
            referenced_from=(
                str(manifest_path),
                manifest.line_of.get("task", 1),
            ),
            detail={"task": task_value, "param_keys": sorted(_param_keys(params))},
        )
    )

    return graph


def _param_keys(params: Any) -> set[str]:
    if isinstance(params, dict):
        return {str(k) for k in params}
    return set()


def _as_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _looks_like_file_path(value: str) -> bool:
    """Return True if the value looks like a file path."""
    if "/" in value or "\\" in value:
        return True
    _, ext = os.path.splitext(value.lower())
    return ext in _POTENTIAL_EXTENSIONS


_POTENTIAL_EXTENSIONS = frozenset(
    {
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".py",
        ".pb",
        ".onnx",
        ".pt",
        ".pth",
        ".bin",
        ".cif",
        ".xyz",
        ".poscar",
        ".contcar",
    }
)


# --- Preflight diagnostics -------------------------------------------------


def preflight_diagnostics(
    case_dir: Path,
    *,
    intent: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], ArtifactGraph]:
    """Run universal generated-input preflight checks.

    Returns a tuple of (diagnostics, artifact_graph). Diagnostics are envelope
    dicts carrying the full ``DiagnosticEnvelope/v1`` field set so the agent
    CLI can emit them directly without re-shaping.
    """
    case_dir = case_dir.resolve()
    manifest_path = find_manifest(case_dir)
    if manifest_path is None:
        # No manifest: nothing to preflight. The legacy analyzer already emits
        # the "no supported files" error, so preflight stays silent rather than
        # duplicating it.
        return [], ArtifactGraph(case_dir=case_dir)
    manifest = _parse_manifest_at(manifest_path)
    if manifest is None:
        return [], ArtifactGraph(case_dir=case_dir)
    graph = build_artifact_graph(case_dir, manifest)

    version_assumption = resolve_version_assumption(intent)
    diagnostics: list[dict[str, Any]] = []
    diagnostics.extend(_missing_required_key_diagnostics(manifest))
    diagnostics.extend(_missing_artifact_diagnostics(graph))
    diagnostics.extend(_unresolved_artifact_diagnostics(graph))
    diagnostics.extend(_model_family_diagnostics(manifest))
    diagnostics.extend(_task_param_diagnostics(manifest))
    diagnostics.extend(_unsupported_structure_diagnostics(manifest))
    diagnostics.extend(_suspicious_task_params_diagnostics(manifest, intent))
    diagnostics.extend(_model_engine_incompatibility_diagnostics(manifest))
    diagnostics.extend(_version_assumption_diagnostic(version_assumption, intent))

    return sorted(
        diagnostics,
        key=lambda item: (
            item.get("range", {}).get("start", {}).get("line", 0),
            item.get("range", {}).get("start", {}).get("character", 0),
            item["code"],
        ),
    ), graph


def _diag(
    *,
    code: str,
    severity: str,
    message: str,
    path: Path,
    line: int = 1,
    column: int = 1,
    category: str,
    confidence: float,
    blocking: bool,
    source_provenance: dict[str, Any],
    fix_hints: list[str],
    actions: list[dict[str, Any]] | None = None,
    facts: dict[str, Any] | None = None,
    artifact_roles: list[str] | None = None,
    domain_tags: list[str] | None = None,
    version_assumption: dict[str, Any] | None = None,
    manual_ref: str | None = None,
    intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a single normalized preflight diagnostic.

    Carries every field the issue acceptance criteria require (``code``,
    ``severity``, ``path``/``range``, ``blocking``, ``category``,
    ``source_provenance``, ``fix_hints``/``actions``) plus the richer envelope
    fields (``facts``, ``artifact_roles``, ``domain_tags``,
    ``version_assumption``) used by the parent fleet probe.
    """
    line0 = max(line - 1, 0)
    col0 = max(column - 1, 0)
    payload: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "message": message,
        "file": str(path),
        "line": line,
        "column": column,
        "category": category,
        "confidence": confidence,
        "source": "mlip-preflight",
        "range": {
            "start": {"line": line0, "character": col0},
            "end": {"line": line0, "character": col0 + 1},
        },
        "blocking": blocking,
        "fix_hints": fix_hints,
        "source_provenance": source_provenance,
    }
    if actions:
        payload["actions"] = actions
    if facts:
        payload["facts"] = facts
    if artifact_roles:
        payload["artifact_roles"] = artifact_roles
    if domain_tags:
        payload["domain_tags"] = domain_tags
    if version_assumption:
        payload["version_assumption"] = version_assumption
    if manual_ref:
        payload["manual_ref"] = manual_ref
    if intent:
        payload["intent"] = intent
    return payload


def _missing_required_key_diagnostics(manifest: ParsedManifest) -> list[dict[str, Any]]:
    """Flag the cross-artifact required-key absence from the graph perspective.

    The legacy analyzer already emits MLIP-E082/083/084 for these, so this
    preflight layer surfaces the same gap as a non-blocking *information*
    diagnostic tagged with the artifact role. This keeps the preflight envelope
    self-describing without duplicating the blocking legacy error.
    """
    out: list[dict[str, Any]] = []
    role_for_key = {
        "model": ROLE_MODEL_POTENTIAL,
        "task": ROLE_TASK_PARAMETERS,
        "structure": ROLE_STRUCTURE,
    }
    for key, role in role_for_key.items():
        if key in manifest.data:
            continue
        line = manifest.line_of.get(key, 1)
        out.append(
            _diag(
                code=CODE_MISSING_REQUIRED_KEY,
                severity="information",
                message=(f"manifest has no '{key}' entry; the {role} artifact role is unresolved"),
                path=manifest.path,
                line=line,
                category="schema",
                confidence=0.9,
                blocking=False,
                source_provenance={
                    "role": role,
                    "key": key,
                    "manifest": str(manifest.path),
                },
                fix_hints=[f"Add a '{key}' entry to the manifest"],
                actions=[
                    {
                        "kind": "add_key",
                        "key": key,
                        "target": str(manifest.path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"missing_key": key, "role": role},
                artifact_roles=[role, ROLE_PRIMARY_INPUT],
                domain_tags=["schema", "cross-artifact"],
            )
        )
    return out


def _missing_artifact_diagnostics(graph: ArtifactGraph) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    # Only block on primary structural artifacts referenced from the manifest.
    # Required-key absence has its own information diagnostic; this check fires
    # only when a reference IS declared but the file is missing.
    for role in (ROLE_STRUCTURE, ROLE_MODEL_POTENTIAL):
        for node in graph.by_role(role):
            if node.exists:
                continue
            ref = node.referenced_from or ("case-root", 1)
            out.append(
                _diag(
                    code=CODE_MISSING_ARTIFACT,
                    severity="error",
                    message=(
                        f"{role} artifact referenced from manifest is missing: {node.path.name}"
                    ),
                    path=node.path,
                    line=ref[1],
                    category="cross-file reference",
                    confidence=0.97,
                    blocking=True,
                    source_provenance={
                        "role": role,
                        "referenced_from": {"path": ref[0], "line": ref[1]},
                        "declared_in": node.source,
                    },
                    fix_hints=[
                        f"Create {node.path.name} in the case directory",
                        f"Or update the manifest reference that points to {node.path.name}",
                    ],
                    actions=[
                        {
                            "kind": "create_artifact",
                            "role": role,
                            "target": str(node.path),
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={"missing_path": str(node.path)},
                    artifact_roles=[role],
                    domain_tags=["cross-file", "blocking"],
                )
            )
    return out


def _unresolved_artifact_diagnostics(graph: ArtifactGraph) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    # The training-config role is optional, so an unresolved reference is a
    # warning rather than a hard block.
    for node in graph.by_role(ROLE_TRAINING_CONFIG):
        if node.exists:
            continue
        ref = node.referenced_from or ("case-root", 1)
        out.append(
            _diag(
                code=CODE_UNRESOLVED_ARTIFACT,
                severity="warning",
                message=(
                    f"{ROLE_TRAINING_CONFIG} artifact referenced from manifest "
                    f"cannot be resolved: {node.path.name}"
                ),
                path=node.path,
                line=ref[1],
                category="cross-file reference",
                confidence=0.85,
                blocking=False,
                source_provenance={
                    "role": ROLE_TRAINING_CONFIG,
                    "declared_in": node.source,
                    "declared": (node.detail or {}).get("declared"),
                },
                fix_hints=[
                    f"Place {node.path.name} in the case directory",
                    "Or remove the training-config reference if it is unused",
                ],
                actions=[
                    {
                        "kind": "resolve_artifact",
                        "role": ROLE_TRAINING_CONFIG,
                        "target": str(node.path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"unresolved_path": str(node.path)},
                artifact_roles=[ROLE_TRAINING_CONFIG],
                domain_tags=["cross-file", "workspace-resolve"],
            )
        )
    return out


def _model_family_diagnostics(manifest: ParsedManifest) -> list[dict[str, Any]]:
    """Validate the declared model against the builtin family/engine registry.

    The model field can be either a known family name (version-aware-keywords
    capability: schema-derived availability) or a weights file path (handled by
    the cross-artifact-graph check). Here we only inspect the named-family form.
    """
    out: list[dict[str, Any]] = []
    model_value = _as_str(manifest.data.get("model"))
    if model_value is None or _looks_like_file_path(model_value):
        return out
    line = manifest.line_of.get("model", 1)
    family = MODEL_FAMILIES.get(model_value)
    if family is None:
        out.append(
            _diag(
                code=CODE_MODEL_FAMILY_MISMATCH,
                severity="warning",
                message=(
                    f"unknown MLIP model family '{model_value}'; known families: "
                    f"{', '.join(sorted(MODEL_FAMILIES))}"
                ),
                path=manifest.path,
                line=line,
                category="semantic consistency",
                confidence=0.8,
                blocking=False,
                source_provenance={
                    "role": ROLE_MODEL_POTENTIAL,
                    "model": model_value,
                    "schema_source": "mlip-lsp builtin MODEL_FAMILIES",
                },
                fix_hints=[
                    "Use a known model family name",
                    "Or point 'model' at the trained weights file directly",
                ],
                actions=[
                    {
                        "kind": "set_key",
                        "key": "model",
                        "value": next(iter(sorted(MODEL_FAMILIES))),
                        "target": str(manifest.path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={
                    "declared_model": model_value,
                    "known_families": sorted(MODEL_FAMILIES),
                },
                artifact_roles=[ROLE_MODEL_POTENTIAL, ROLE_PRIMARY_INPUT],
                domain_tags=["semantic", "version-aware"],
            )
        )
    return out


def _task_param_diagnostics(manifest: ParsedManifest) -> list[dict[str, Any]]:
    """Validate that the declared task has the parameters its contract requires."""
    out: list[dict[str, Any]] = []
    task_value = _as_str(manifest.data.get("task"))
    if task_value is None or task_value not in TASK_REQUIREMENTS:
        return out
    required = TASK_REQUIREMENTS[task_value]
    if not required:
        return out
    params = manifest.data.get("parameters")
    param_keys = _param_keys(params)
    missing = [key for key in required if key not in param_keys]
    if not missing:
        return out
    line = manifest.line_of.get("task", 1)
    out.append(
        _diag(
            code=CODE_TASK_PARAM_MISMATCH,
            severity="error",
            message=(f"task '{task_value}' is missing required parameter(s): {', '.join(missing)}"),
            path=manifest.path,
            line=line,
            category="cross-file reference",
            confidence=0.9,
            blocking=True,
            source_provenance={
                "role": ROLE_TASK_PARAMETERS,
                "task": task_value,
                "required_params": list(required),
                "provided_params": sorted(param_keys),
                "schema_source": "mlip-lsp builtin TASK_REQUIREMENTS",
            },
            fix_hints=[
                f"Add the missing parameter(s) under 'parameters': {', '.join(missing)}",
                f"Or switch to a task that does not require {', '.join(missing)}",
            ],
            actions=[
                {
                    "kind": "add_parameter",
                    "parameter": missing[0],
                    "target": str(manifest.path),
                    "safe_to_auto_apply": False,
                }
            ],
            facts={
                "task": task_value,
                "required_params": list(required),
                "missing": missing,
            },
            artifact_roles=[ROLE_TASK_PARAMETERS, ROLE_PRIMARY_INPUT],
            domain_tags=["cross-artifact", "blocking"],
        )
    )
    return out


def _unsupported_structure_diagnostics(manifest: ParsedManifest) -> list[dict[str, Any]]:
    """Flag structure references whose extension the engines cannot consume."""
    out: list[dict[str, Any]] = []
    structure_value = _as_str(manifest.data.get("structure"))
    if structure_value is None:
        return out
    _, ext = os.path.splitext(structure_value.lower())
    if not ext or ext in STRUCTURE_EXTENSIONS:
        return out
    line = manifest.line_of.get("structure", 1)
    out.append(
        _diag(
            code=CODE_UNSUPPORTED_STRUCTURE_EXT,
            severity="warning",
            message=(
                f"structure file '{structure_value}' has unsupported extension "
                f"'{ext}'; expected one of: {', '.join(sorted(STRUCTURE_EXTENSIONS))}"
            ),
            path=manifest.path,
            line=line,
            category="type/value",
            confidence=0.85,
            blocking=False,
            source_provenance={
                "role": ROLE_STRUCTURE,
                "declared": structure_value,
                "extension": ext,
                "schema_source": "mlip-lsp builtin STRUCTURE_EXTENSIONS",
            },
            fix_hints=[
                "Convert the structure to a supported format",
                "Or correct the file extension in the manifest",
            ],
            actions=[
                {
                    "kind": "set_key",
                    "key": "structure",
                    "value": structure_value + ".cif",
                    "target": str(manifest.path),
                    "safe_to_auto_apply": False,
                }
            ],
            facts={
                "declared": structure_value,
                "extension": ext,
                "supported": sorted(STRUCTURE_EXTENSIONS),
            },
            artifact_roles=[ROLE_STRUCTURE, ROLE_PRIMARY_INPUT],
            domain_tags=["type/value", "version-aware"],
        )
    )
    return out


# Engines whose task surface is constrained relative to the general dp/mace
# engines. Used by the version-aware engine/task compatibility check so the
# finding is schema-derived rather than guessed. The gpumd engine (NEP) only
# exposes md/static via its native driver; geometry optimization is routed
# differently and should be flagged so the parent probe can branch.
_ENGINE_TASK_CONSTRAINTS: dict[str, set[str]] = {
    "gpumd": {"md", "static"},
}


def _model_engine_incompatibility_diagnostics(
    manifest: ParsedManifest,
) -> list[dict[str, Any]]:
    """Flag a declared model whose engine does not support the declared task.

    Version-aware-keywords capability: the builtin ``MODEL_FAMILIES`` registry
    records each family's execution engine, and ``_ENGINE_TASK_CONSTRAINTS``
    records the constrained task surface for engines whose surface is narrower
    than the general dp/mace engines. When the declared task is outside the
    engine's surface the finding is a real, schema-derived compatibility gap.
    """
    out: list[dict[str, Any]] = []
    model_value = _as_str(manifest.data.get("model"))
    task_value = _as_str(manifest.data.get("task"))
    if model_value is None or task_value is None:
        return out
    if _looks_like_file_path(model_value):
        return out
    family = MODEL_FAMILIES.get(model_value)
    if family is None:
        return out
    engine = str(family.get("engine", "")).lower()
    allowed = _ENGINE_TASK_CONSTRAINTS.get(engine)
    if allowed is None or task_value in allowed:
        return out
    line = manifest.line_of.get("model", 1)
    version_assumption = resolve_version_assumption(None)
    out.append(
        _diag(
            code=CODE_MODEL_ENGINE_INCOMPATIBLE,
            severity="error",
            message=(
                f"model family '{model_value}' runs on the {engine} engine which "
                f"does not support task '{task_value}' (supported: "
                f"{', '.join(sorted(allowed))})"
            ),
            path=manifest.path,
            line=line,
            category="semantic consistency",
            confidence=0.9,
            blocking=True,
            source_provenance={
                "role": ROLE_MODEL_POTENTIAL,
                "cross_referenced_role": ROLE_TASK_PARAMETERS,
                "model": model_value,
                "engine": engine,
                "task": task_value,
                "engine_task_surface": sorted(allowed),
                "schema_source": "mlip-lsp builtin MODEL_FAMILIES",
            },
            fix_hints=[
                f"Switch the task to one supported by {engine}: {', '.join(sorted(allowed))}",
                "Or choose a model family whose engine supports this task",
            ],
            actions=[
                {
                    "kind": "set_key",
                    "key": "task",
                    "value": next(iter(sorted(allowed))),
                    "target": str(manifest.path),
                    "safe_to_auto_apply": False,
                }
            ],
            facts={
                "model": model_value,
                "engine": engine,
                "task": task_value,
                "engine_task_surface": sorted(allowed),
            },
            artifact_roles=[ROLE_MODEL_POTENTIAL, ROLE_TASK_PARAMETERS],
            domain_tags=["version-aware", "blocking"],
            version_assumption=version_assumption,
            manual_ref="mlip-lsp builtin MODEL_FAMILIES",
        )
    )
    return out


def _suspicious_task_params_diagnostics(
    manifest: ParsedManifest, intent: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """Heuristic risk flags on common silent-bad-result parameter values.

    These are warnings: the values parse and type-check, but they risk silently
    inaccurate results (e.g. an MD run at zero temperature, or absurdly few
    steps). The intent contract can opt out by declaring the run as a smoke
    test.
    """
    out: list[dict[str, Any]] = []
    params = manifest.data.get("parameters")
    if not isinstance(params, dict):
        return out
    smoke_test = bool((intent or {}).get("smoke_test", False))
    task_value = _as_str(manifest.data.get("task"))
    line = manifest.line_of.get("task", 1)

    if task_value == "md":
        temperature = _as_number(params.get("temperature"))
        steps = _as_int(params.get("steps"))
        findings: list[str] = []
        if temperature is not None and temperature <= 0:
            findings.append(f"temperature={temperature} is non-positive")
        if steps is not None and 0 < steps < 10:
            findings.append(f"steps={steps} is suspiciously low for an MD trajectory")
        if findings and not smoke_test:
            out.append(
                _diag(
                    code=CODE_SUSPICIOUS_TASK_PARAMS,
                    severity="warning",
                    message=("md task has suspicious parameter(s): " + "; ".join(findings)),
                    path=manifest.path,
                    line=line,
                    category="preflight/runtime-risk",
                    confidence=0.7,
                    blocking=False,
                    source_provenance={
                        "role": ROLE_TASK_PARAMETERS,
                        "task": task_value,
                        "findings": findings,
                    },
                    fix_hints=[
                        "Review the flagged MD parameters before running",
                        "Or mark the run as a smoke test in the intent contract",
                    ],
                    actions=[
                        {
                            "kind": "review_key",
                            "key": "parameters",
                            "target": str(manifest.path),
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={"task": task_value, "findings": findings},
                    artifact_roles=[ROLE_TASK_PARAMETERS],
                    domain_tags=["preflight", "runtime-risk"],
                )
            )
    return out


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


# --- version-aware-keywords ------------------------------------------------


def resolve_version_assumption(intent: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve the explicit runtime/version assumption for this preflight run.

    When the exact runtime/image version is unknown we record that fact
    explicitly rather than guessing, per the issue's version-assumptions
    acceptance criterion. The intent contract can override ``software_version``
    (e.g. ``mlip-sdk >=2024``); otherwise we fall back to the schema version the
    builtin model/task registry was authored against.
    """
    intent = intent or {}
    software_version = intent.get("software_version")
    runtime_image = intent.get("runtime_image")
    assumption: dict[str, Any] = {
        "software": "mlip",
        "software_version": software_version or "unknown",
        "runtime_image": runtime_image or "unknown",
        "schema_source": intent.get("schema_source", "mlip-lsp builtin"),
        # The fallback is intentional and explicit so consumers never have to
        # guess whether ``unknown`` means "not checked" or "could not determine".
        "exact_runtime_known": bool(software_version or runtime_image),
    }
    if software_version or runtime_image:
        assumption["declared_by"] = "intent"
    else:
        assumption["declared_by"] = "fallback"
    return assumption


def _version_assumption_diagnostic(
    version_assumption: dict[str, Any], intent: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """Emit an explicit information diagnostic when the runtime version is unknown.

    This makes the version assumption machine-readable in the diagnostic stream
    itself (not just metadata) so the parent probe can surface it without
    parsing the envelope top-level.
    """
    if version_assumption["exact_runtime_known"]:
        return []
    return [
        _diag(
            code=CODE_VERSION_ASSUMPTION,
            severity="information",
            message=(
                "Exact MLIP SDK/runtime image version is unknown; preflight "
                "validated against the builtin model/task registry"
            ),
            path=Path(version_assumption.get("schema_source", "mlip-lsp builtin")),
            line=1,
            category="preflight/runtime-risk",
            confidence=1.0,
            blocking=False,
            source_provenance={
                "role": ROLE_PRIMARY_INPUT,
                "reason": "software_version and runtime_image not declared in intent",
            },
            fix_hints=[
                "Declare software_version/runtime_image in the intent contract",
            ],
            actions=[],
            facts={
                "software_version": version_assumption["software_version"],
                "runtime_image": version_assumption["runtime_image"],
                "schema_source": version_assumption["schema_source"],
            },
            artifact_roles=[ROLE_PRIMARY_INPUT],
            domain_tags=["version-aware", "assumption"],
            version_assumption=version_assumption,
            intent=dict(intent) if intent else None,
        )
    ]


# --- fleet-regression-fixtures --------------------------------------------


def fleet_manifest(
    *,
    fixtures: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a machine-readable preflight manifest for the parent fleet.

    The parent ``bohrium_skills`` probe/report workflow consumes this to know
    which preflight codes exist, which capabilities are implemented, and which
    fixtures exercise them. Keeping it as data (not README prose) means the
    fleet regression evidence stays in sync with the implementation.
    """
    codes = {
        CODE_MISSING_ARTIFACT: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "referenced structure/model-potential file missing from workspace",
        },
        CODE_MODEL_FAMILY_MISMATCH: {
            "severity": "warning",
            "category": "semantic consistency",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "declared model family not in builtin registry",
        },
        CODE_TASK_PARAM_MISMATCH: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "task is missing a parameter its contract requires",
        },
        CODE_UNRESOLVED_ARTIFACT: {
            "severity": "warning",
            "category": "cross-file reference",
            "blocking": False,
            "capability": "cross-artifact-graph",
            "summary": "optional training-config reference cannot be resolved",
        },
        CODE_MISSING_REQUIRED_KEY: {
            "severity": "information",
            "category": "schema",
            "blocking": False,
            "capability": "cross-artifact-graph",
            "summary": "manifest is missing a key the artifact-role model expects",
        },
        CODE_UNSUPPORTED_STRUCTURE_EXT: {
            "severity": "warning",
            "category": "type/value",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "structure file extension not in builtin supported set",
        },
        CODE_SUSPICIOUS_TASK_PARAMS: {
            "severity": "warning",
            "category": "preflight/runtime-risk",
            "blocking": False,
            "capability": "cross-artifact-graph",
            "summary": "task parameter values risk silently inaccurate results",
        },
        CODE_VERSION_ASSUMPTION: {
            "severity": "information",
            "category": "preflight/runtime-risk",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "exact runtime version unknown; fallback schema used",
        },
        CODE_MODEL_ENGINE_INCOMPATIBLE: {
            "severity": "error",
            "category": "semantic consistency",
            "blocking": True,
            "capability": "version-aware-keywords",
            "summary": "declared model engine incompatible with the task",
        },
    }
    capabilities = {
        "version-aware-keywords": {
            "status": "available",
            "evidence_codes": [
                CODE_MODEL_FAMILY_MISMATCH,
                CODE_UNSUPPORTED_STRUCTURE_EXT,
                CODE_VERSION_ASSUMPTION,
            ],
        },
        "cross-artifact-graph": {
            "status": "available",
            "roles": list(ALL_ROLES),
            "evidence_codes": [
                CODE_MISSING_ARTIFACT,
                CODE_TASK_PARAM_MISMATCH,
                CODE_UNRESOLVED_ARTIFACT,
                CODE_MISSING_REQUIRED_KEY,
                CODE_SUSPICIOUS_TASK_PARAMS,
            ],
        },
        "code-actions": {
            "status": "available",
            "blocking_gate": "mlip-lsp-tool check --fail-on-blocking",
            "evidence_codes": list(codes.keys()),
        },
        "fleet-regression-fixtures": {
            "status": "available",
            "fixtures": list(fixtures) if fixtures else [],
        },
    }
    return {
        "software": "mlip",
        "preflight_envelope": f"DiagnosticEnvelope/{DIAGNOSTIC_ENVELOPE_VERSION}",
        "artifact_roles": list(ALL_ROLES),
        "capabilities": capabilities,
        "codes": codes,
    }
