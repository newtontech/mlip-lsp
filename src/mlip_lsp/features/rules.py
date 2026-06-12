"""MLIP diagnostic rules with MLIP-prefixed codes.

Rule code assignment:
  MLIP-E080  mlip.json.invalid         – JSON manifest cannot be parsed
  MLIP-E081  mlip.yaml.invalid         – YAML manifest cannot be parsed
  MLIP-E082  mlip.manifest.missing_model      – manifest lacks 'model' key
  MLIP-E083  mlip.manifest.missing_task       – manifest lacks 'task' key
  MLIP-E084  mlip.manifest.missing_structure   – manifest lacks 'structure' key
  MLIP-W080  mlip.python.missing_ase_import    – Python script missing ASE import
  MLIP-E085  mlip.python.missing_structure_symbol – Python script missing 'structure' symbol
  MLIP-E086  mlip.files.missing_path_reference – manifest references a file that does not exist
  MLIP-E087  mlip.log.traceback         – runtime log contains a Python traceback
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    """A single diagnostic rule definition."""

    code: str
    name: str
    severity: str
    message_template: str
    category: str


# ---------------------------------------------------------------------------
# Canonical rule table
# ---------------------------------------------------------------------------

RULES: dict[str, Rule] = {
    "MLIP-E080": Rule(
        code="MLIP-E080",
        name="mlip.json.invalid",
        severity="error",
        message_template="JSON manifest cannot be parsed: {detail}",
        category="syntax",
    ),
    "MLIP-E081": Rule(
        code="MLIP-E081",
        name="mlip.yaml.invalid",
        severity="error",
        message_template="YAML manifest cannot be parsed: {detail}",
        category="syntax",
    ),
    "MLIP-E082": Rule(
        code="MLIP-E082",
        name="mlip.manifest.missing_model",
        severity="error",
        message_template="manifest is missing required key 'model'",
        category="schema",
    ),
    "MLIP-E083": Rule(
        code="MLIP-E083",
        name="mlip.manifest.missing_task",
        severity="error",
        message_template="manifest is missing required key 'task'",
        category="schema",
    ),
    "MLIP-E084": Rule(
        code="MLIP-E084",
        name="mlip.manifest.missing_structure",
        severity="error",
        message_template="manifest is missing required key 'structure'",
        category="schema",
    ),
    "MLIP-W080": Rule(
        code="MLIP-W080",
        name="mlip.python.missing_ase_import",
        severity="warning",
        message_template="expected import or symbol 'ase' was not found",
        category="schema",
    ),
    "MLIP-E085": Rule(
        code="MLIP-E085",
        name="mlip.python.missing_structure_symbol",
        severity="error",
        message_template="expected workflow symbol 'structure' was not found",
        category="schema",
    ),
    "MLIP-E086": Rule(
        code="MLIP-E086",
        name="mlip.files.missing_path_reference",
        severity="warning",
        message_template="manifest references file '{path}' which does not exist",
        category="cross-file reference",
    ),
    "MLIP-E087": Rule(
        code="MLIP-E087",
        name="mlip.log.traceback",
        severity="error",
        message_template="runtime log contains a Python traceback starting at line {line}",
        category="preflight/runtime-risk",
    ),
}


def get_rule(code: str) -> Rule | None:
    """Look up a rule by its MLIP-prefixed code."""
    return RULES.get(code)


def format_message(code: str, **kwargs: str) -> str:
    """Format the message template for a rule with the given parameters."""
    rule = RULES.get(code)
    if rule is None:
        return kwargs.get("detail", "unknown diagnostic")
    return rule.message_template.format(**kwargs)
