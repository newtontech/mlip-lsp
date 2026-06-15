"""Provenance manifest and capability manifest contract tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS = REPO_ROOT / "raw" / "assets"
MANIFEST_PATH = ASSETS / "manifest.json"
CAPS_PATH = REPO_ROOT / "lsp-capabilities.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_provenance_manifest_schema_and_checksums() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "provenance-manifest-v1"
    assert manifest["repository"] == "newtontech/mlip-lsp"
    assert len(manifest.get("official_source_anchors", [])) >= 1
    entries = manifest.get("entries", [])
    assert entries, "manifest must list at least one raw asset entry"

    for entry in entries:
        asset_path = ASSETS / entry["path"]
        assert asset_path.is_file(), f"missing raw asset: {entry['path']}"
        assert entry["checksum_sha256"] == _sha256(asset_path), entry["path"]
        assert entry.get("stable_id"), f"stable_id required for {entry['path']}"
        assert entry.get("retrieval_date"), f"retrieval_date required for {entry['path']}"
        for wiki_link in entry.get("wiki_links", []):
            assert (REPO_ROOT / wiki_link).is_file(), wiki_link


def test_lsp_capabilities_llm_wiki_and_fixture_paths() -> None:
    caps = json.loads(CAPS_PATH.read_text(encoding="utf-8"))
    llm_wiki = caps["llmWiki"]
    assert (REPO_ROOT / llm_wiki["upstreamManifest"]).is_file()
    assert (REPO_ROOT / llm_wiki["provenanceManifest"]).is_file()
    assert (REPO_ROOT / llm_wiki["agentContext"]).is_file()
    for example in llm_wiki["exampleInputs"]:
        assert (REPO_ROOT / example).is_file(), example

    coverage = caps.get("diagnostic_coverage", {})
    assert coverage.get("status") == "partial"

    fixture_paths = caps.get("fixturePaths", {})
    for category in ("valid", "invalid"):
        paths = fixture_paths.get(category, [])
        assert paths, f"fixturePaths.{category} must be non-empty"
        assert any((REPO_ROOT / rel).exists() for rel in paths), category


def test_capabilities_cli_includes_source_provenance(capsys) -> None:
    from mlip_lsp import tool

    assert tool.main(["capabilities"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload.get("sourceProvenance", [])) >= 1
    assert payload["llmWiki"]["provenanceManifest"] == "raw/assets/manifest.json"
