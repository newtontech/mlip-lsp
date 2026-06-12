"""Safe formatter for MLIP manifest files (JSON, YAML, text).

Guarantees:
  1. Never raises – returns the original text on any parse/format failure.
  2. Idempotent: format(format(text)) == format(text).
  3. Preserves trailing newline convention.
"""

from __future__ import annotations

import json
import re
from typing import Any

import yaml


def _safe_json_loads(text: str) -> Any | None:
    """Try to parse JSON; return None on failure."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def _safe_json_dumps(obj: Any) -> str:
    """Serialize to pretty-printed JSON with a trailing newline."""
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _safe_yaml_load(text: str) -> Any | None:
    """Try to parse YAML; return None on failure."""
    try:
        return yaml.safe_load(text)
    except Exception:
        return None


def _safe_yaml_dumps(obj: Any) -> str:
    """Serialize to YAML with a trailing newline."""
    try:
        return str(
            yaml.dump(
                obj,
                default_flow_style=False,
                sort_keys=True,
                allow_unicode=True,
            )
        )
    except Exception:
        return ""


def format_json(text: str) -> str:
    """Format JSON manifest. Returns original on failure."""
    obj = _safe_json_loads(text)
    if obj is None:
        return text
    return _safe_json_dumps(obj)


def format_yaml(text: str) -> str:
    """Format YAML manifest. Returns original on failure."""
    obj = _safe_yaml_load(text)
    if obj is None:
        return text
    formatted = _safe_yaml_dumps(obj)
    return formatted if formatted else text


def format_text(text: str) -> str:
    """Format MLIP text config with aligned key=value pairs.

    This is the original NEP-style text formatter, preserved for
    backward compatibility.
    """
    lines: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith(("#", "!", ";")):
            lines.append(raw.rstrip())
            continue
        if "=" in stripped:
            key, value = stripped.split("=", 1)
            lines.append(f"{key.strip():<24} = {value.strip()}")
        else:
            parts = stripped.split(maxsplit=1)
            if len(parts) == 2 and re.match(r"^[A-Za-z_][A-Za-z0-9_\-.]*$", parts[0]):
                lines.append(f"{parts[0]:<24} {parts[1].strip()}")
            else:
                lines.append(stripped)
    return "\n".join(lines).rstrip() + "\n"


def safe_format(text: str, file_suffix: str) -> str:
    """Dispatch formatting by file type. Never raises.

    Parameters
    ----------
    text:
        The file content to format.
    file_suffix:
        Lowercase suffix including the dot, e.g. ".json", ".yaml", ".txt".
    """
    suffix = file_suffix.lower()
    if suffix == ".json":
        return format_json(text)
    if suffix in (".yaml", ".yml"):
        return format_yaml(text)
    return format_text(text)


def is_idempotent(text: str, file_suffix: str) -> bool:
    """Check that formatting is idempotent for the given content."""
    first = safe_format(text, file_suffix)
    second = safe_format(first, file_suffix)
    return first == second
