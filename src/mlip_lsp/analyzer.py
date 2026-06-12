from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from .diagnostics import Diagnostic
from .features.formatter import format_text as format_text
from .features.log_parser import log_diagnostics
from .features.matmaster import (
    validate_manifest_structure,
)

DOMAIN_NAME = "MLIP"
DOMAIN_ID = "mlip"
DOMAIN_KIND = "json"
CODE_PREFIX = "MLIP"
FILE_PATTERNS: list[str] = ["*.json", "*.yaml", "*.yml", "*.py", "*.log"]
FILE_NAMES: list[str] = []
FILE_SUFFIXES: list[str] = [".json", ".yaml", ".yml", ".py", ".log"]
KNOWN_TOKENS: list[str] = []
REQUIRED_TOKENS: list[str] = []
REQUIRED_IMPORTS: list[str] = ["ase"]
REQUIRED_SYMBOLS: list[str] = ["structure"]
REQUIRED_JSON_KEYS: list[str] = ["model", "structure", "task"]

COMMENT_PREFIXES = ("#", "!", ";")

# ---------------------------------------------------------------------------
# Path reference helpers
# ---------------------------------------------------------------------------

_FILE_PATH_EXTENSIONS = frozenset(
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


def _looks_like_file_path(value: str) -> bool:
    """Return True if the value looks like a file path."""
    if "/" in value or "\\" in value:
        return True
    _, ext = os.path.splitext(value.lower())
    return ext in _FILE_PATH_EXTENSIONS


# ---------------------------------------------------------------------------
# Top-level analysis API
# ---------------------------------------------------------------------------


def analyze_path(path: Path) -> list[Diagnostic]:
    path = path.resolve()
    files = _collect_files(path)
    diagnostics: list[Diagnostic] = []
    if not files:
        diagnostics.append(
            Diagnostic(
                code=f"{CODE_PREFIX}201",
                severity="error",
                message=f"no supported {DOMAIN_NAME} files found",
                file=str(path),
                line=1,
            )
        )
        return diagnostics
    for file_path in files:
        diagnostics.extend(analyze_file(file_path))
    return sorted(diagnostics, key=lambda item: (item.file, item.line, item.code))


def _collect_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if _is_supported(path) else []
    result: list[Path] = []
    for pattern in FILE_PATTERNS:
        result.extend(path.rglob(pattern))
    return sorted({item for item in result if item.is_file()})


def _is_supported(path: Path) -> bool:
    name = path.name.lower()
    suffix = path.suffix.lower()
    return (
        name in FILE_NAMES
        or suffix in FILE_SUFFIXES
        or any(path.match(pattern) for pattern in FILE_PATTERNS)
    )


def analyze_file(path: Path) -> list[Diagnostic]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [
            Diagnostic(f"{CODE_PREFIX}202", "error", "file is not valid UTF-8 text", str(path), 1)
        ]
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _analyze_json(path, content)
    if suffix in (".yaml", ".yml"):
        return _analyze_yaml(path, content)
    if suffix == ".py":
        return _analyze_python(path, content)
    if suffix == ".log":
        return log_diagnostics(content, str(path))
    return _analyze_text(path, content)


# ---------------------------------------------------------------------------
# JSON analysis (MLIP-E080, E082, E083, E084, E086)
# ---------------------------------------------------------------------------


def _analyze_json(path: Path, content: str) -> list[Diagnostic]:
    """Analyze a JSON manifest with MLIP-prefixed codes."""
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        return [
            Diagnostic(
                "MLIP-E080",
                "error",
                f"JSON manifest cannot be parsed: {exc.msg}",
                str(path),
                exc.lineno,
                exc.colno,
                suggested_fix={"kind": "fix_json_syntax", "detail": exc.msg},
                confidence=0.95,
            )
        ]
    diagnostics: list[Diagnostic] = []
    if isinstance(payload, dict):
        diagnostics.extend(validate_manifest_structure(payload, str(path)))
        diagnostics.extend(_check_path_references(payload, path))
    return diagnostics


# ---------------------------------------------------------------------------
# YAML analysis (MLIP-E081, E082, E083, E084, E086)
# ---------------------------------------------------------------------------


def _analyze_yaml(path: Path, content: str) -> list[Diagnostic]:
    """Analyze a YAML manifest with MLIP-prefixed codes."""
    try:
        payload = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        detail = str(exc) if exc else "unknown YAML error"
        line = 1
        if hasattr(exc, "problem_mark") and exc.problem_mark is not None:
            line = exc.problem_mark.line + 1
        return [
            Diagnostic(
                "MLIP-E081",
                "error",
                f"YAML manifest cannot be parsed: {detail}",
                str(path),
                line,
                suggested_fix={"kind": "fix_yaml_syntax", "detail": detail},
                confidence=0.95,
            )
        ]
    diagnostics: list[Diagnostic] = []
    if isinstance(payload, dict):
        diagnostics.extend(validate_manifest_structure(payload, str(path)))
        diagnostics.extend(_check_path_references(payload, path))
    return diagnostics


# ---------------------------------------------------------------------------
# Cross-file path reference check (MLIP-E086)
# ---------------------------------------------------------------------------


def _check_path_references(payload: dict[str, Any], manifest_path: Path) -> list[Diagnostic]:
    """Check that file references in the manifest exist (MLIP-E086).

    Only checks 'structure' (always a file) and 'model' (only when it looks
    like an actual file path with a recognized extension).
    """
    diagnostics: list[Diagnostic] = []
    manifest_dir = manifest_path.parent

    # structure is always a file reference
    value = payload.get("structure")
    if isinstance(value, str):
        referenced = manifest_dir / value
        if not referenced.exists():
            diagnostics.append(
                Diagnostic(
                    "MLIP-E086",
                    "warning",
                    f"manifest references file '{value}' which does not exist",
                    str(manifest_path),
                    1,
                    evidence=[f"Key 'structure' references '{value}'"],
                    suggested_fix={"kind": "create_missing_file", "path": value},
                    confidence=0.8,
                )
            )

    # model is checked only if it looks like a file path
    model = payload.get("model")
    if isinstance(model, str) and _looks_like_file_path(model):
        referenced = manifest_dir / model
        if not referenced.exists():
            diagnostics.append(
                Diagnostic(
                    "MLIP-E086",
                    "warning",
                    f"manifest references file '{model}' which does not exist",
                    str(manifest_path),
                    1,
                    evidence=[f"Key 'model' references '{model}'"],
                    suggested_fix={"kind": "create_missing_file", "path": model},
                    confidence=0.7,
                )
            )

    return diagnostics


# ---------------------------------------------------------------------------
# Python analysis (MLIP-W080, MLIP-E085)
# ---------------------------------------------------------------------------


def _analyze_python(path: Path, content: str) -> list[Diagnostic]:
    """Analyze a Python script with MLIP-prefixed codes."""
    diagnostics: list[Diagnostic] = []
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        return [
            Diagnostic("MLIP-E080", "error", exc.msg, str(path), exc.lineno or 1, exc.offset or 1)
        ]
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    imports = _import_names(tree)

    # MLIP-W080: missing ASE import
    if "ase" not in imports and "ase" not in names:
        diagnostics.append(
            Diagnostic(
                "MLIP-W080",
                "warning",
                "expected import or symbol 'ase' was not found",
                str(path),
                1,
                suggested_fix={"kind": "add_import", "module": "ase"},
                confidence=0.75,
            )
        )

    # MLIP-E085: missing structure symbol
    if "structure" not in names and "structure" not in attrs and "structure" not in content:
        diagnostics.append(
            Diagnostic(
                "MLIP-E085",
                "error",
                "expected workflow symbol 'structure' was not found",
                str(path),
                1,
                suggested_fix={"kind": "add_symbol", "symbol": "structure"},
                confidence=0.68,
            )
        )

    return diagnostics


# ---------------------------------------------------------------------------
# Text analysis (NEP configs, etc.)
# ---------------------------------------------------------------------------


def _analyze_text(path: Path, content: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    meaningful = _meaningful_lines(content)
    present = {line.split()[0].lower() for _, line in meaningful if line.split()}
    for required in REQUIRED_TOKENS:
        if required.lower() not in present and required.lower() not in content.lower():
            diagnostics.append(
                Diagnostic(
                    f"{CODE_PREFIX}101",
                    "warning",
                    f"expected {DOMAIN_NAME} token or setting '{required}' was not found",
                    str(path),
                    1,
                    evidence=["MVP rule derived from MatMaster execution contracts"],
                    suggested_fix={"kind": "add_required_token", "token": required},
                    confidence=0.72,
                )
            )
    for line_no, line in meaningful:
        token = line.split()[0].lower()
        if KNOWN_TOKENS and token not in KNOWN_TOKENS and not token.startswith(("#", "&", "%")):
            diagnostics.append(
                Diagnostic(
                    f"{CODE_PREFIX}001",
                    "warning",
                    f"unknown or currently unsupported {DOMAIN_NAME} keyword: {token}",
                    str(path),
                    line_no,
                    suggested_fix={"kind": "check_keyword_spelling", "keyword": token},
                    confidence=0.55,
                )
            )
    return diagnostics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _import_names(tree: ast.AST) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module.split(".")[0])
    return result


def _meaningful_lines(content: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for line_no, raw in enumerate(content.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith(COMMENT_PREFIXES):
            continue
        result.append((line_no, stripped))
    return result
