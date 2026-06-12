"""pygls-based LSP server for MLIP workflow manifests and ASE scripts."""

from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from lsprotocol.types import (
    TEXT_DOCUMENT_CODE_ACTION,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_FORMATTING,
    TEXT_DOCUMENT_HOVER,
    CodeAction,
    CodeActionKind,
    CodeActionParams,
    Command,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionParams,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentFormattingParams,
    Hover,
    HoverParams,
    MarkupContent,
    MarkupKind,
    OptionalVersionedTextDocumentIdentifier,
    Position,
    Range,
    TextDocumentEdit,
    TextEdit,
    WorkspaceEdit,
)
from lsprotocol.types import (
    Diagnostic as LspDiagnostic,
)
from pygls.server import LanguageServer

from .analyzer import REQUIRED_JSON_KEYS, format_text
from .diagnostics import Diagnostic
from .features.formatter import safe_format
from .features.log_parser import log_diagnostics

# ---------------------------------------------------------------------------
# LSP diagnostic / completion / hover helpers
# ---------------------------------------------------------------------------

MANIFEST_KEY_DOCS: dict[str, str] = {
    "model": "MLIP model identifier (e.g. DPA3.1-3M, MACE, NEP).",
    "structure": "Path to the input structure file (CIF, POSCAR, XYZ, etc.).",
    "task": "Computation task type (optimize, md, static, relax, etc.).",
    "parameters": "Dictionary of simulation parameters (temperature, steps, etc.).",
    "output": "Dictionary specifying output file paths and options.",
}

KNOWN_MLIP_MODELS = [
    "DPA3.1-3M",
    "DPA2",
    "MACE",
    "NEP",
    "CHGNet",
    "M3GNet",
    "SevenNet",
    "ORB",
]

TASK_TYPES = [
    "optimize",
    "md",
    "static",
    "relax",
    "phonon",
    "neb",
    "transition_state",
]

PYTHON_COMPLETION_SNIPPETS = {
    "from ase import ": [
        "Atoms",
        "Atom",
        "io",
    ],
    "from ase.optimize import ": [
        "BFGS",
        "LBFGS",
        "FIRE",
    ],
    "from mlip import ": [
        "MLIPCalculator",
    ],
}

# Extended hover docs for Python symbols
PYTHON_HOVER_DOCS: dict[str, str] = {
    "ase": "**ASE**  \nAtomic Simulation Environment for atomistic simulations.",
    "Atoms": "**Atoms**  \nASE object representing a collection of atoms.",
    "structure": (
        "**structure**  \nExpected ASE Atoms object for MLIP workflow with a .calc attribute."
    ),
    "BFGS": "**BFGS**  \nASE optimizer using the BFGS algorithm.",
    "MLIPCalculator": (
        "**MLIPCalculator**  \nASE calculator wrapping an MLIP model for energy/force predictions."
    ),
    "calc": (
        "**calc**  \nASE calculator attached to an Atoms object for DFT or MLIP computations."
    ),
    "FIRE": "**FIRE**  \nASE optimizer using the FIRE algorithm.",
    "LBFGS": "**LBFGS**  \nASE optimizer using the Limited-memory BFGS algorithm.",
}


def _uri_to_path(uri: str) -> str:
    """Convert a file:// URI to a local path string."""
    if uri.startswith("file://"):
        path = uri[7:]
        # Handle Windows-style paths (file:///C:/...)
        if path and path[0] == "/" and len(path) > 2 and path[2] == ":":
            path = path[1:]
        return path
    return uri


def _compute_diagnostics_for_uri(uri: str, content: str) -> list[Diagnostic]:
    """Compute diagnostics for the given document content."""
    path = Path(_uri_to_path(uri))
    suffix = path.suffix.lower()

    if suffix == ".json":
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            return [
                Diagnostic(
                    "MLIP-E080",
                    "error",
                    f"JSON manifest cannot be parsed: {exc.msg}",
                    _uri_to_path(uri),
                    exc.lineno,
                    exc.colno,
                    suggested_fix={"kind": "fix_json_syntax", "detail": exc.msg},
                    confidence=0.95,
                )
            ]
        yaml_diagnostics: list[Diagnostic] = []
        if isinstance(payload, dict):
            key_to_code = {"model": "MLIP-E082", "task": "MLIP-E083", "structure": "MLIP-E084"}
            for key, code in key_to_code.items():
                if key not in payload:
                    yaml_diagnostics.append(
                        Diagnostic(
                            code,
                            "error",
                            f"manifest is missing required key '{key}'",
                            _uri_to_path(uri),
                            1,
                            suggested_fix={"kind": "add_json_key", "key": key},
                            confidence=0.9,
                        )
                    )
            # MLIP-E086: check path references
            yaml_diagnostics.extend(_check_path_refs(payload, path, uri))
        return yaml_diagnostics

    if suffix in (".yaml", ".yml"):
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
                    _uri_to_path(uri),
                    line,
                    suggested_fix={"kind": "fix_yaml_syntax", "detail": detail},
                    confidence=0.95,
                )
            ]
        diagnostics: list[Diagnostic] = []
        if isinstance(payload, dict):
            key_to_code = {"model": "MLIP-E082", "task": "MLIP-E083", "structure": "MLIP-E084"}
            for key, code in key_to_code.items():
                if key not in payload:
                    diagnostics.append(
                        Diagnostic(
                            code,
                            "error",
                            f"manifest is missing required key '{key}'",
                            _uri_to_path(uri),
                            1,
                            suggested_fix={"kind": "add_json_key", "key": key},
                            confidence=0.9,
                        )
                    )
            diagnostics.extend(_check_path_refs(payload, path, uri))
        return diagnostics

    if suffix == ".py":
        try:
            tree = ast.parse(content)
        except SyntaxError as exc:
            return [
                Diagnostic(
                    "MLIP-E080",
                    "error",
                    exc.msg,
                    _uri_to_path(uri),
                    exc.lineno or 1,
                    exc.offset or 1,
                )
            ]
        py_diags: list[Diagnostic] = []
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        # MLIP-W080: missing ASE import
        if "ase" not in imports and "ase" not in names:
            py_diags.append(
                Diagnostic(
                    "MLIP-W080",
                    "warning",
                    "expected import or symbol 'ase' was not found",
                    _uri_to_path(uri),
                    1,
                    suggested_fix={"kind": "add_import", "module": "ase"},
                    confidence=0.75,
                )
            )

        # MLIP-E085: missing structure symbol
        if "structure" not in names and "structure" not in attrs and "structure" not in content:
            py_diags.append(
                Diagnostic(
                    "MLIP-E085",
                    "error",
                    "expected workflow symbol 'structure' was not found",
                    _uri_to_path(uri),
                    1,
                    suggested_fix={"kind": "add_symbol", "symbol": "structure"},
                    confidence=0.68,
                )
            )

        return py_diags

    if suffix == ".log":
        return log_diagnostics(content, _uri_to_path(uri))

    return []


def _looks_like_file_path(value: str) -> bool:
    """Return True if the value looks like a file path (has recognized extension or slash)."""
    if "/" in value or "\\" in value:
        return True
    known_extensions = {
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
    _, ext = os.path.splitext(value.lower())
    return ext in known_extensions


def _check_path_refs(payload: dict[str, Any], manifest_path: Path, uri: str) -> list[Diagnostic]:
    """Check cross-file path references for MLIP-E086."""
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
                    _uri_to_path(uri),
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
                    _uri_to_path(uri),
                    1,
                    evidence=[f"Key 'model' references '{model}'"],
                    suggested_fix={"kind": "create_missing_file", "path": model},
                    confidence=0.7,
                )
            )

    return diagnostics


def _compute_completions(uri: str, content: str, line: int, character: int) -> list[CompletionItem]:
    """Compute completion items for the given position."""
    path = Path(_uri_to_path(uri))
    suffix = path.suffix.lower()

    if suffix == ".json":
        lines = content.splitlines()
        current_line = lines[line] if line < len(lines) else ""
        text_before = current_line[:character]

        if text_before.rstrip().endswith(",") or text_before.rstrip().endswith("{"):
            try:
                payload = json.loads(content)
                existing_keys = set(payload) if isinstance(payload, dict) else set()
            except (json.JSONDecodeError, ValueError):
                existing_keys = set()

            items: list[CompletionItem] = []
            for key in REQUIRED_JSON_KEYS:
                if key not in existing_keys:
                    items.append(
                        CompletionItem(
                            label=key,
                            kind=CompletionItemKind.Property,
                            detail=f"Required manifest key: {key}",
                            documentation=MANIFEST_KEY_DOCS.get(key, ""),
                        )
                    )
            for key in ("parameters", "output"):
                if key not in existing_keys:
                    items.append(
                        CompletionItem(
                            label=key,
                            kind=CompletionItemKind.Property,
                            detail=f"Optional manifest key: {key}",
                            documentation=MANIFEST_KEY_DOCS.get(key, ""),
                        )
                    )
            return items

        model_match = re.search(r'"model"\s*:\s*"([^"]*)$', text_before)
        if model_match:
            prefix = model_match.group(1)
            return [
                CompletionItem(
                    label=model,
                    kind=CompletionItemKind.Value,
                    detail=f"MLIP model: {model}",
                )
                for model in KNOWN_MLIP_MODELS
                if model.lower().startswith(prefix.lower())
            ]

        task_match = re.search(r'"task"\s*:\s*"([^"]*)$', text_before)
        if task_match:
            prefix = task_match.group(1)
            return [
                CompletionItem(
                    label=task,
                    kind=CompletionItemKind.Value,
                    detail=f"Task type: {task}",
                )
                for task in TASK_TYPES
                if task.lower().startswith(prefix.lower())
            ]

    if suffix in (".yaml", ".yml"):
        lines = content.splitlines()
        current_line = lines[line] if line < len(lines) else ""
        stripped = current_line.strip()

        # Suggest top-level keys
        if ":" not in stripped or stripped.endswith(":"):
            word = stripped.rstrip(":").strip()
            if not word:
                yaml_items: list[CompletionItem] = []
                for key in REQUIRED_JSON_KEYS:
                    yaml_items.append(
                        CompletionItem(
                            label=f"{key}:",
                            kind=CompletionItemKind.Property,
                            detail=f"Required manifest key: {key}",
                            documentation=MANIFEST_KEY_DOCS.get(key, ""),
                        )
                    )
                for key in ("parameters", "output"):
                    yaml_items.append(
                        CompletionItem(
                            label=f"{key}:",
                            kind=CompletionItemKind.Property,
                            detail=f"Optional manifest key: {key}",
                            documentation=MANIFEST_KEY_DOCS.get(key, ""),
                        )
                    )
                return yaml_items

    if suffix == ".py":
        lines = content.splitlines()
        current_line = lines[line] if line < len(lines) else ""
        text_before = current_line[:character]

        for prefix_str, options in PYTHON_COMPLETION_SNIPPETS.items():
            if text_before.strip().startswith(
                prefix_str.rstrip(" ")
            ) or text_before.strip().startswith(prefix_str):
                return [
                    CompletionItem(
                        label=opt,
                        kind=CompletionItemKind.Module,
                        detail=f"Import: {prefix_str}{opt}",
                    )
                    for opt in options
                    if opt.lower().startswith(
                        text_before.strip()[len(prefix_str.rstrip(" ")) :].lower()
                    )
                ]

        if "from " in text_before and "import " not in text_before:
            return [
                CompletionItem(label=f"from {m} import ", kind=CompletionItemKind.Module)
                for m in ["ase", "ase.optimize", "ase.io", "mlip", "numpy", "torch"]
            ]

    return []


def _compute_hover(uri: str, content: str, line: int, character: int) -> str | None:
    """Compute hover information for the given position."""
    path = Path(_uri_to_path(uri))
    suffix = path.suffix.lower()

    lines = content.splitlines()
    if line >= len(lines):
        return None
    current_line = lines[line]
    if character >= len(current_line):
        return None

    if suffix == ".json":
        key_match = re.match(r'\s*"([^"]+)"\s*:', current_line)
        if key_match:
            key = key_match.group(1)
            if key in MANIFEST_KEY_DOCS:
                return f"**{key}**  \n{MANIFEST_KEY_DOCS[key]}"
            if key == "model":
                models_str = ", ".join(KNOWN_MLIP_MODELS)
                return f"**model**  \nMLIP model identifier. Known models: {models_str}"

        model_val_match = re.search(r'"model"\s*:\s*"([^"]*)"', current_line)
        if model_val_match and model_val_match.start() <= character <= model_val_match.end():
            val = model_val_match.group(1)
            if val in KNOWN_MLIP_MODELS:
                return (
                    f"**{val}**  \nMLIP potential model. See MatMaster documentation for details."
                )

        task_val_match = re.search(r'"task"\s*:\s*"([^"]*)"', current_line)
        if task_val_match and task_val_match.start() <= character <= task_val_match.end():
            val = task_val_match.group(1)
            return f"**{val}**  \nMLIP computation task type."

    if suffix in (".yaml", ".yml"):
        stripped = current_line.strip()
        if ":" in stripped:
            key = stripped.split(":")[0].strip()
            if key in MANIFEST_KEY_DOCS:
                return f"**{key}**  \n{MANIFEST_KEY_DOCS[key]}"
            if key == "model":
                models_str = ", ".join(KNOWN_MLIP_MODELS)
                return f"**model**  \nMLIP model identifier. Known models: {models_str}"

    # Extract word at cursor
    word_start = character
    while word_start > 0 and re.match(r"[\w.]", current_line[word_start - 1]):
        word_start -= 1
    word_end = character
    while word_end < len(current_line) and re.match(r"[\w.]", current_line[word_end]):
        word_end += 1
    word = current_line[word_start:word_end] if word_end > word_start else ""

    if word and suffix == ".py":
        doc = PYTHON_HOVER_DOCS.get(word)
        if doc:
            return doc

    return None


def _compute_code_actions(
    uri: str, content: str, diagnostics: list[Diagnostic]
) -> list[CodeAction | Command]:
    """Compute code actions with proper WorkspaceEdit support."""
    actions: list[CodeAction | Command] = []
    path = Path(_uri_to_path(uri))
    suffix = path.suffix.lower()

    for diag in diagnostics:
        fix = diag.suggested_fix
        if fix is None:
            continue
        kind = fix.get("kind", "")

        if kind == "add_json_key" and suffix == ".json":
            key = fix.get("key", "")
            title = f"Add missing key '{key}'"
            try:
                payload = json.loads(content) if content.strip() else {}
            except json.JSONDecodeError:
                payload = {}
            if isinstance(payload, dict) and key not in payload:
                payload[key] = ""
                new_text = json.dumps(payload, indent=2) + "\n"
                lines = content.splitlines()
                last_line = max(len(lines) - 1, 0)
                last_char = len(lines[-1]) if lines else 0
                actions.append(
                    CodeAction(
                        title=title,
                        kind=CodeActionKind.QuickFix,
                        edit=WorkspaceEdit(
                            document_changes=[
                                TextDocumentEdit(
                                    text_document=OptionalVersionedTextDocumentIdentifier(
                                        uri=uri, version=None
                                    ),
                                    edits=[
                                        TextEdit(
                                            range=Range(
                                                start=Position(line=0, character=0),
                                                end=Position(line=last_line, character=last_char),
                                            ),
                                            new_text=new_text,
                                        )
                                    ],
                                )
                            ]
                        ),
                        diagnostics=None,
                    )
                )

        elif kind == "add_json_key" and suffix in (".yaml", ".yml"):
            key = fix.get("key", "")
            title = f"Add missing key '{key}'"
            try:
                payload = yaml.safe_load(content) if content.strip() else {}
            except yaml.YAMLError:
                payload = {}
            if isinstance(payload, dict) and key not in payload:
                payload[key] = ""
                new_text = yaml.dump(payload, default_flow_style=False, sort_keys=True)
                lines = content.splitlines()
                last_line = max(len(lines) - 1, 0)
                last_char = len(lines[-1]) if lines else 0
                actions.append(
                    CodeAction(
                        title=title,
                        kind=CodeActionKind.QuickFix,
                        edit=WorkspaceEdit(
                            document_changes=[
                                TextDocumentEdit(
                                    text_document=OptionalVersionedTextDocumentIdentifier(
                                        uri=uri, version=None
                                    ),
                                    edits=[
                                        TextEdit(
                                            range=Range(
                                                start=Position(line=0, character=0),
                                                end=Position(line=last_line, character=last_char),
                                            ),
                                            new_text=new_text,
                                        )
                                    ],
                                )
                            ]
                        ),
                        diagnostics=None,
                    )
                )

        elif kind == "add_import" and suffix == ".py":
            module = fix.get("module", "")
            title = f"Add import for '{module}'"
            new_text = f"from {module} import Atoms\n{content}"
            lines = content.splitlines()
            last_line = max(len(lines) - 1, 0)
            last_char = len(lines[-1]) if lines else 0
            actions.append(
                CodeAction(
                    title=title,
                    kind=CodeActionKind.QuickFix,
                    edit=WorkspaceEdit(
                        document_changes=[
                            TextDocumentEdit(
                                text_document=OptionalVersionedTextDocumentIdentifier(
                                    uri=uri, version=None
                                ),
                                edits=[
                                    TextEdit(
                                        range=Range(
                                            start=Position(line=0, character=0),
                                            end=Position(line=last_line, character=last_char),
                                        ),
                                        new_text=new_text,
                                    )
                                ],
                            )
                        ]
                    ),
                    diagnostics=None,
                )
            )

        elif kind == "add_symbol" and suffix == ".py":
            symbol = fix.get("symbol", "")
            title = f"Add symbol '{symbol}'"
            new_text = f"{content}\n{symbol} = None  # TODO: define {symbol}\n"
            lines = content.splitlines()
            last_line = max(len(lines) - 1, 0)
            last_char = len(lines[-1]) if lines else 0
            actions.append(
                CodeAction(
                    title=title,
                    kind=CodeActionKind.QuickFix,
                    edit=WorkspaceEdit(
                        document_changes=[
                            TextDocumentEdit(
                                text_document=OptionalVersionedTextDocumentIdentifier(
                                    uri=uri, version=None
                                ),
                                edits=[
                                    TextEdit(
                                        range=Range(
                                            start=Position(line=0, character=0),
                                            end=Position(line=last_line, character=last_char),
                                        ),
                                        new_text=new_text,
                                    )
                                ],
                            )
                        ]
                    ),
                    diagnostics=None,
                )
            )

    return actions


# ---------------------------------------------------------------------------
# MLIPServer class
# ---------------------------------------------------------------------------


class MLIPServer:
    """MLIP Language Server wrapping pygls with domain-specific features."""

    def __init__(self) -> None:
        self.server = LanguageServer(
            name="mlip-lsp",
            version="0.1.0",
        )
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register LSP feature handlers on the pygls server."""
        server = self.server

        @server.feature(TEXT_DOCUMENT_DID_OPEN)
        def did_open(params: DidOpenTextDocumentParams) -> None:
            uri = params.text_document.uri
            content = params.text_document.text
            self._publish_diagnostics(uri, content)

        @server.feature(TEXT_DOCUMENT_DID_CHANGE)
        def did_change(params: DidChangeTextDocumentParams) -> None:
            uri = params.text_document.uri
            content = params.content_changes[-1].text
            self._publish_diagnostics(uri, content)

        @server.feature(TEXT_DOCUMENT_COMPLETION)
        def completion(params: CompletionParams) -> CompletionList | None:
            uri = params.text_document.uri
            doc = server.workspace.get_text_document(uri)
            items = _compute_completions(
                uri,
                doc.source,
                params.position.line,
                params.position.character,
            )
            return CompletionList(is_incomplete=False, items=items)

        @server.feature(TEXT_DOCUMENT_HOVER)
        def hover(params: HoverParams) -> Hover | None:
            uri = params.text_document.uri
            doc = server.workspace.get_text_document(uri)
            result = _compute_hover(
                uri,
                doc.source,
                params.position.line,
                params.position.character,
            )
            if result:
                return Hover(
                    contents=MarkupContent(
                        kind=MarkupKind.Markdown,
                        value=result,
                    )
                )
            return None

        @server.feature(TEXT_DOCUMENT_FORMATTING)
        def formatting(params: DocumentFormattingParams) -> list[TextEdit] | None:
            uri = params.text_document.uri
            try:
                doc = server.workspace.get_text_document(uri)
                suffix = Path(_uri_to_path(uri)).suffix.lower()
                formatted = safe_format(doc.source, suffix)
                if formatted == doc.source:
                    return None
                lines = doc.source.splitlines()
                last_line = max(len(lines) - 1, 0)
                last_char = len(lines[-1]) if lines else 0
                return [
                    TextEdit(
                        range=Range(
                            start=Position(line=0, character=0),
                            end=Position(line=last_line, character=last_char),
                        ),
                        new_text=formatted,
                    )
                ]
            except Exception:
                return None

        @server.feature(TEXT_DOCUMENT_CODE_ACTION)
        def code_action(params: CodeActionParams) -> list[CodeAction | Command] | None:
            uri = params.text_document.uri
            doc = server.workspace.get_text_document(uri)
            our_diags = _compute_diagnostics_for_uri(uri, doc.source)
            actions = _compute_code_actions(uri, doc.source, our_diags)
            return actions if actions else None

    def _publish_diagnostics(self, uri: str, content: str) -> None:
        """Publish diagnostics for a document."""
        diags = self.compute_diagnostics(uri, content)
        lsp_diags: list[LspDiagnostic] = []
        for d in diags:
            lsp_diags.append(
                LspDiagnostic(
                    range=Range(
                        start=Position(line=max(d.line - 1, 0), character=max(d.column - 1, 0)),
                        end=Position(line=max(d.line - 1, 0), character=1000),
                    ),
                    severity=(
                        DiagnosticSeverity.Error
                        if d.severity == "error"
                        else DiagnosticSeverity.Warning
                    ),
                    code=d.code,
                    message=d.message,
                    source="mlip-lsp",
                )
            )
        self.server.publish_diagnostics(uri, lsp_diags)

    # ------------------------------------------------------------------
    # Public API (used by tests and externally)
    # ------------------------------------------------------------------

    def compute_diagnostics(self, uri: str, content: str) -> list[Diagnostic]:
        """Compute diagnostics for the given document content."""
        return _compute_diagnostics_for_uri(uri, content)

    def complete(self, uri: str, content: str, line: int, character: int) -> list[dict[str, Any]]:
        """Compute completion items (returns dicts for test compatibility)."""
        items = _compute_completions(uri, content, line, character)
        return [
            {
                "label": item.label,
                "kind": item.kind,
                "detail": item.detail or "",
            }
            for item in items
        ]

    def hover(self, uri: str, content: str, line: int, character: int) -> str | None:
        """Compute hover information."""
        return _compute_hover(uri, content, line, character)

    def format(self, content: str) -> str:
        """Format document content."""
        return format_text(content)


def create_server() -> MLIPServer:
    """Create and return an MLIPServer instance."""
    return MLIPServer()
