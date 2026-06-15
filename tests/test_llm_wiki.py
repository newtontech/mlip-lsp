"""LLM wiki and capability manifest sanity checks."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_lsp_capabilities_llm_wiki_paths_exist() -> None:
    caps = json.loads((REPO_ROOT / "lsp-capabilities.json").read_text(encoding="utf-8"))
    llm_wiki = caps["llmWiki"]
    assert (REPO_ROOT / llm_wiki["upstreamManifest"]).is_file()
    assert (REPO_ROOT / llm_wiki["provenanceManifest"]).is_file()
    assert (REPO_ROOT / llm_wiki["agentContext"]).is_file()
    for example in llm_wiki["exampleInputs"]:
        assert (REPO_ROOT / example).is_file(), example


def test_upstream_manifest_lists_examples() -> None:
    manifest = (REPO_ROOT / "raw/assets/upstream-sources.md").read_text(encoding="utf-8")
    assert "manifest_md.json" in manifest
    assert "mlip.skoltech.ru" in manifest
