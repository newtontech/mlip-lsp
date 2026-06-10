"""pygls-based LSP server for MLIP workflow manifests and ASE scripts."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

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
    Position,
    PublishDiagnosticsParams,
    Range,
    TextEdit,
)
from lsprotocol.types import (
    Diagnostic as LspDiagnostic,
)
from pygls.lsp.server import LanguageServer

from .analyzer import REQUIRED_JSON_KEYS, format_text
from .diagnostics import Diagnostic

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
                    "MLIP001",
                    "error",
                    exc.msg,
                    _uri_to_path(uri),
                    exc.lineno,
                    exc.colno,
                )
            ]
        diagnostics: list[Diagnostic] = []
        if isinstance(payload, dict):
            for key in REQUIRED_JSON_KEYS:
                if key not in payload:
                    diagnostics.append(
                        Diagnostic(
                            "MLIP101",
                            "warning",
                            f"manifest is missing required key '{key}'",
                            _uri_to_path(uri),
                            1,
                            suggested_fix={"kind": "add_json_key", "key": key},
                            confidence=0.78,
                        )
                    )
        return diagnostics

    if suffix == ".py":
        try:
            tree = ast.parse(content)
        except SyntaxError as exc:
            return [
                Diagnostic(
                    "MLIP001",
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
        # Check Import statements explicitly
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        if "ase" not in imports and "ase" not in names:
            py_diags.append(
                Diagnostic(
                    "MLIP101",
                    "warning",
                    "expected import or symbol 'ase' was not found",
                    _uri_to_path(uri),
                    1,
                    suggested_fix={"kind": "add_import", "module": "ase"},
                    confidence=0.75,
                )
            )

        if "structure" not in names and "structure" not in attrs and "structure" not in content:
            py_diags.append(
                Diagnostic(
                    "MLIP102",
                    "warning",
                    "expected workflow symbol 'structure' was not found",
                    _uri_to_path(uri),
                    1,
                    confidence=0.68,
                )
            )

        return py_diags

    return []


def _compute_completions(uri: str, content: str, line: int, character: int) -> list[CompletionItem]:
    """Compute completion items for the given position."""
    path = Path(_uri_to_path(uri))
    suffix = path.suffix.lower()

    if suffix == ".json":
        # Try to determine if we're inside a JSON object and suggest keys
        lines = content.splitlines()
        current_line = lines[line] if line < len(lines) else ""
        text_before = current_line[:character]

        # Check if we're at a position where a key would be typed
        # (after a comma or opening brace)
        if text_before.rstrip().endswith(",") or text_before.rstrip().endswith("{"):
            # Parse existing keys to avoid suggesting duplicates
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
            # Also suggest optional keys
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

        # Check if we're typing a value and should suggest model names
        # Simple heuristic: look for "model": " before cursor
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

        # Suggest task values
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

    if suffix == ".py":
        lines = content.splitlines()
        current_line = lines[line] if line < len(lines) else ""
        text_before = current_line[:character]

        # Complete common import patterns
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

        # Generic import completion
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
        # Check if we're hovering over a JSON key
        # Find the key under cursor
        key_match = re.match(r'\s*"([^"]+)"\s*:', current_line)
        if key_match:
            key = key_match.group(1)
            if key in MANIFEST_KEY_DOCS:
                return f"**{key}**  \n{MANIFEST_KEY_DOCS[key]}"
            if key == "model":
                models_str = ", ".join(KNOWN_MLIP_MODELS)
                return f"**model**  \nMLIP model identifier. Known models: {models_str}"

        # Check if hovering over a model value
        model_val_match = re.search(r'"model"\s*:\s*"([^"]*)"', current_line)
        if model_val_match and model_val_match.start() <= character <= model_val_match.end():
            val = model_val_match.group(1)
            if val in KNOWN_MLIP_MODELS:
                return (
                    f"**{val}**  \nMLIP potential model. See MatMaster documentation for details."
                )

        # Check if hovering over a task value
        task_val_match = re.search(r'"task"\s*:\s*"([^"]*)"', current_line)
        if task_val_match and task_val_match.start() <= character <= task_val_match.end():
            val = task_val_match.group(1)
            return f"**{val}**  \nMLIP computation task type."

    # General keyword hover for any file type
    word = current_line[character : character + 1]
    # Try to find the word at cursor
    word_start = character
    while word_start > 0 and re.match(r"[\w.]", current_line[word_start - 1]):
        word_start -= 1
    word_end = character
    while word_end < len(current_line) and re.match(r"[\w.]", current_line[word_end]):
        word_end += 1
    word = current_line[word_start:word_end] if word_end > word_start else ""

    if word:
        if suffix == ".py":
            if word == "ase":
                return "**ASE**  \nAtomic Simulation Environment for atomistic simulations."
            if word == "Atoms":
                return "**Atoms**  \nASE object representing a collection of atoms."
            if word == "structure":
                return (
                    "**structure**  \n"
                    "Expected ASE Atoms object for MLIP workflow with a .calc attribute."
                )
            if word == "BFGS":
                return "**BFGS**  \nASE optimizer using the BFGS algorithm."
            if word == "MLIPCalculator":
                return (
                    "**MLIPCalculator**  \n"
                    "ASE calculator wrapping an MLIP model for energy/force predictions."
                )
            if word == "calc":
                return (
                    "**calc**  \n"
                    "ASE calculator attached to an Atoms object for DFT or MLIP computations."
                )

    return None


def _compute_code_actions(
    uri: str, content: str, diagnostics: list[Diagnostic]
) -> list[CodeAction | Command]:
    """Compute code actions based on diagnostics."""
    actions: list[CodeAction | Command] = []
    path = Path(_uri_to_path(uri))
    suffix = path.suffix.lower()

    for diag in diagnostics:
        if diag.code == "MLIP101" and diag.suggested_fix:
            fix = diag.suggested_fix
            kind = fix.get("kind", "")
            if kind == "add_json_key" and suffix == ".json":
                key = fix.get("key", "")
                title = f"Add missing key '{key}'"
                # Create a text edit that adds the key
                try:
                    payload = json.loads(content) if content.strip() else {}
                except json.JSONDecodeError:
                    payload = {}
                if isinstance(payload, dict) and key not in payload:
                    # Add the key to the JSON
                    actions.append(
                        CodeAction(
                            title=title,
                            kind=CodeActionKind.QuickFix,
                            edit=None,  # Simplified: edit needs workspace edit
                            diagnostics=None,
                        )
                    )
            elif kind == "add_import" and suffix == ".py":
                module = fix.get("module", "")
                title = f"Add import for '{module}'"
                actions.append(
                    CodeAction(
                        title=title,
                        kind=CodeActionKind.QuickFix,
                        edit=None,
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
            # Use the full content from the last change event
            content = params.content_changes[-1].text
            self._publish_diagnostics(uri, content)

        @server.feature(TEXT_DOCUMENT_COMPLETION)
        def completion(params: CompletionParams) -> CompletionList | None:
            uri = params.text_document.uri
            # We need access to the document content
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
                formatted = format_text(doc.source)
                if formatted == doc.source:
                    return None
                # Return a single edit replacing the entire document
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
        self.server.text_document_publish_diagnostics(
            PublishDiagnosticsParams(uri=uri, diagnostics=lsp_diags)
        )

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
