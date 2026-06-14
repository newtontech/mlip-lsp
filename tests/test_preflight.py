from __future__ import annotations

import json
from pathlib import Path

import pytest

from mlip_lsp import tool
from mlip_lsp.preflight import (
    ALL_ROLES,
    CODE_MISSING_ARTIFACT,
    CODE_MISSING_REQUIRED_KEY,
    CODE_MODEL_ENGINE_INCOMPATIBLE,
    CODE_MODEL_FAMILY_MISMATCH,
    CODE_SUSPICIOUS_TASK_PARAMS,
    CODE_TASK_PARAM_MISMATCH,
    CODE_UNRESOLVED_ARTIFACT,
    CODE_UNSUPPORTED_STRUCTURE_EXT,
    CODE_VERSION_ASSUMPTION,
    ArtifactGraph,
    build_artifact_graph,
    find_manifest,
    fleet_manifest,
    resolve_version_assumption,
)
from mlip_lsp.tool import (
    _dedupe_preflight,
    _looks_like_workspace,
    check_path,
    manifest_path,
    preflight_path,
)

FIXTURES = Path(__file__).parent / "fixtures" / "preflight"

# Envelope fields the issue acceptance criteria require on failing fixtures.
REQUIRED_FAILING_FIELDS = {
    "code",
    "severity",
    "path",
    "range",
    "blocking",
    "category",
    "source_provenance",
}


def _envelope_codes(payload: dict) -> set[str]:
    return {item["code"] for item in payload["diagnostics"]}


# --- Envelope shape --------------------------------------------------------


def test_agent_check_payload_carries_diagnostic_envelope_v1(capsys) -> None:
    # exercise the real CLI path so the capabilities block is attached
    rc = tool.main(["check", str(FIXTURES / "task_param_mismatch")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["diagnostic_envelope"] == "v1"
    assert payload["diagnostic_engine"] == "1.0"
    assert payload["software"] == "mlip"
    # capabilities block is attached by the CLI wrapper
    assert payload["capabilities"]["operation"] == "check"
    # version assumption is surfaced at top level so the parent probe can branch
    assert "version_assumption" in payload
    assert payload["version_assumption"]["software"] == "mlip"
    # cross-artifact graph is serialized for the fleet report workflow
    assert isinstance(payload.get("artifacts"), list)
    assert payload["artifacts"]


def test_failing_diagnostics_carry_required_envelope_fields() -> None:
    payload = preflight_path(FIXTURES / "task_param_mismatch")
    failing = [item for item in payload["diagnostics"] if item["code"] == CODE_TASK_PARAM_MISMATCH]
    assert failing, "task_param_mismatch fixture must emit MLIP603"
    item = failing[0]
    for field in REQUIRED_FAILING_FIELDS:
        assert field in item, f"missing required envelope field: {field}"
    # Richer envelope fields used by the parent fleet probe
    assert item["confidence"] >= 0.0
    assert "actions" in item and item["actions"]
    assert "fix_hints" in item and item["fix_hints"]
    assert "facts" in item
    assert item["facts"]["task"] == "md"
    assert "missing" in item["facts"]
    assert "artifact_roles" in item
    # range is a proper LSP-style start/end object
    assert item["range"]["start"]["line"] >= 0
    assert "character" in item["range"]["start"]


# --- Fixture behavior ------------------------------------------------------


@pytest.mark.parametrize(
    "fixture, expected_ok, must_include, must_exclude_blocking",
    [
        ("valid_manifest", True, set(), set()),
        ("missing_model_potential", False, {CODE_MISSING_ARTIFACT}, set()),
        ("task_param_mismatch", False, {CODE_TASK_PARAM_MISMATCH}, set()),
        (
            "suspicious_md_params",
            True,
            {CODE_SUSPICIOUS_TASK_PARAMS},
            {CODE_SUSPICIOUS_TASK_PARAMS},
        ),
        ("model_engine_incompatible", False, {CODE_MODEL_ENGINE_INCOMPATIBLE}, set()),
        (
            "unresolved_training_config",
            True,
            {CODE_UNRESOLVED_ARTIFACT},
            {CODE_UNRESOLVED_ARTIFACT},
        ),
    ],
)
def test_preflight_fixture_expectations(
    fixture: str,
    expected_ok: bool,
    must_include: set[str],
    must_exclude_blocking: set[str],
) -> None:
    payload = preflight_path(FIXTURES / fixture)
    codes = _envelope_codes(payload)
    assert payload["ok"] is expected_ok, (
        f"{fixture}: expected ok={expected_ok}, got codes={sorted(codes)}"
    )
    assert must_include <= codes, f"{fixture}: expected codes {must_include}, got {sorted(codes)}"
    blocking_codes = {item["code"] for item in payload["diagnostics"] if item["blocking"]}
    assert not (must_exclude_blocking & blocking_codes), (
        f"{fixture}: codes {must_exclude_blocking} must not be blocking"
    )


def test_valid_manifest_fixture_has_no_blocking_or_error_diagnostics() -> None:
    payload = preflight_path(FIXTURES / "valid_manifest")
    assert payload["summary"]["errors"] == 0
    assert payload["summary"]["blocking"] == 0
    # valid fixture must not carry the preflight error codes
    error_codes = {
        CODE_MISSING_ARTIFACT,
        CODE_TASK_PARAM_MISMATCH,
        CODE_MODEL_ENGINE_INCOMPATIBLE,
    }
    assert not (_envelope_codes(payload) & error_codes)


def test_missing_model_potential_is_blocking_error() -> None:
    payload = preflight_path(FIXTURES / "missing_model_potential")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_MISSING_ARTIFACT)
    assert item["severity"] == "error"
    assert item["blocking"] is True
    assert item["artifact_roles"] == ["model-potential"]


def test_model_engine_incompatible_carries_version_assumption() -> None:
    payload = preflight_path(FIXTURES / "model_engine_incompatible")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_MODEL_ENGINE_INCOMPATIBLE)
    assert item["facts"]["model"] == "NEP"
    assert item["facts"]["engine"] == "gpumd"
    assert item["facts"]["task"] == "optimize"
    assert "md" in item["facts"]["engine_task_surface"]
    assert "version-aware" in item["domain_tags"]
    assert "version_assumption" in item


def test_suspicious_md_params_is_non_blocking_warning() -> None:
    payload = preflight_path(FIXTURES / "suspicious_md_params")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_SUSPICIOUS_TASK_PARAMS)
    assert item["severity"] == "warning"
    assert item["blocking"] is False
    findings = item["facts"]["findings"]
    assert any("temperature" in f for f in findings)


def test_suspicious_md_params_silenced_by_smoke_test_intent(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "manifest.json").write_text(
        json.dumps(
            {
                "model": "DPA3.1-3M",
                "structure": "input.cif",
                "task": "md",
                "parameters": {"temperature": -10, "steps": 5},
            }
        ),
        encoding="utf-8",
    )
    (case / "input.cif").write_text("data_Si\n", encoding="utf-8")
    # No intent: suspicious params fire.
    base = preflight_path(case)
    assert CODE_SUSPICIOUS_TASK_PARAMS in _envelope_codes(base)

    cfg = case / ".mlip-lsp"
    cfg.mkdir()
    (cfg / "intent.json").write_text(json.dumps({"smoke_test": True}), encoding="utf-8")
    overridden = preflight_path(case)
    assert CODE_SUSPICIOUS_TASK_PARAMS not in _envelope_codes(overridden)


# --- version-aware-keywords ------------------------------------------------


def test_version_assumption_unknown_when_intent_absent() -> None:
    assumption = resolve_version_assumption(None)
    assert assumption["exact_runtime_known"] is False
    assert assumption["declared_by"] == "fallback"
    assert assumption["software_version"] == "unknown"


def test_version_assumption_known_when_intent_declares_version() -> None:
    assumption = resolve_version_assumption(
        {"software_version": "mlip-sdk >=2024", "runtime_image": "img:2024.1"}
    )
    assert assumption["exact_runtime_known"] is True
    assert assumption["declared_by"] == "intent"
    assert assumption["software_version"] == "mlip-sdk >=2024"


def test_version_assumption_information_diagnostic_when_unknown(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "manifest.json").write_text(
        json.dumps({"model": "DPA3.1-3M", "structure": "input.cif", "task": "optimize"}),
        encoding="utf-8",
    )
    (case / "input.cif").write_text("data_Si\n", encoding="utf-8")
    payload = preflight_path(case)
    item = next(
        (d for d in payload["diagnostics"] if d["code"] == CODE_VERSION_ASSUMPTION),
        None,
    )
    assert item is not None
    assert item["severity"] == "information"
    assert item["blocking"] is False
    assert item["version_assumption"]["exact_runtime_known"] is False


def test_version_assumption_silent_when_intent_declares_version(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "manifest.json").write_text(
        json.dumps({"model": "DPA3.1-3M", "structure": "input.cif", "task": "optimize"}),
        encoding="utf-8",
    )
    (case / "input.cif").write_text("data_Si\n", encoding="utf-8")
    cfg = case / ".mlip-lsp"
    cfg.mkdir()
    (cfg / "intent.json").write_text(
        json.dumps({"software_version": "mlip-sdk >=2024"}), encoding="utf-8"
    )
    payload = preflight_path(case)
    assert CODE_VERSION_ASSUMPTION not in _envelope_codes(payload)
    assert payload["version_assumption"]["exact_runtime_known"] is True


# --- cross-artifact-graph --------------------------------------------------


def test_artifact_graph_uses_generic_roles() -> None:
    from mlip_lsp.preflight import _parse_manifest_at

    case_dir = (FIXTURES / "valid_manifest").resolve()
    manifest = _parse_manifest_at(case_dir / "manifest.json")
    assert manifest is not None
    graph = build_artifact_graph(case_dir, manifest)
    roles = {node.role for node in graph.nodes}
    assert roles <= set(ALL_ROLES)
    # primary-input, structure, task-parameters are always present
    for required in ("primary-input", "structure", "task-parameters"):
        assert graph.by_role(required), f"missing required role: {required}"
    # serialized graph is JSON-friendly and stable
    serialized = graph.to_json()
    assert isinstance(serialized, list)
    assert all("role" in node and "path" in node and "exists" in node for node in serialized)


def test_missing_model_potential_records_provenance() -> None:
    payload = preflight_path(FIXTURES / "missing_model_potential")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_MISSING_ARTIFACT)
    prov = item["source_provenance"]
    assert prov["role"] == "model-potential"
    assert "referenced_from" in prov
    # provenance points back at the manifest that declared the model
    assert prov["referenced_from"]["path"].endswith("manifest.json")


def test_unresolved_training_config_is_warning() -> None:
    payload = preflight_path(FIXTURES / "unresolved_training_config")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_UNRESOLVED_ARTIFACT)
    assert item["severity"] == "warning"
    assert item["artifact_roles"] == ["training-config"]


def test_unknown_model_family_is_warning(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "manifest.json").write_text(
        json.dumps({"model": "NotARealFamily", "structure": "input.cif", "task": "optimize"}),
        encoding="utf-8",
    )
    (case / "input.cif").write_text("data_Si\n", encoding="utf-8")
    payload = preflight_path(case)
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_MODEL_FAMILY_MISMATCH)
    assert item["severity"] == "warning"
    assert item["blocking"] is False


def test_unsupported_structure_extension_is_warning(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "manifest.json").write_text(
        json.dumps({"model": "DPA3.1-3M", "structure": "input.exotic", "task": "optimize"}),
        encoding="utf-8",
    )
    payload = preflight_path(case)
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_UNSUPPORTED_STRUCTURE_EXT)
    assert item["severity"] == "warning"
    assert item["facts"]["extension"] == ".exotic"


def test_missing_required_key_is_information(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    # manifest with no structure key at all (separate from a missing-file reference)
    (case / "manifest.json").write_text(
        json.dumps({"model": "DPA3.1-3M", "task": "optimize"}),
        encoding="utf-8",
    )
    payload = preflight_path(case)
    items = [d for d in payload["diagnostics"] if d["code"] == CODE_MISSING_REQUIRED_KEY]
    assert items
    for item in items:
        assert item["severity"] == "information"
        assert item["blocking"] is False


# --- code-actions / blocking gate -----------------------------------------


def test_check_fail_on_blocking_exits_nonzero_on_failing_fixture() -> None:
    rc = tool.main(["check", str(FIXTURES / "task_param_mismatch"), "--fail-on-blocking"])
    assert rc == 1


def test_check_fail_on_blocking_exits_zero_on_valid_fixture(capsys) -> None:
    rc = tool.main(["check", str(FIXTURES / "valid_manifest"), "--fail-on-blocking"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True


def test_preflight_subcommand_emits_envelope(capsys) -> None:
    rc = tool.main(["preflight", str(FIXTURES / "suspicious_md_params")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operation"] == "preflight"
    assert payload["diagnostic_envelope"] == "v1"
    assert payload["capabilities"]["operation"] == "preflight"


def test_actions_present_on_blocking_diagnostics() -> None:
    payload = preflight_path(FIXTURES / "task_param_mismatch")
    blocking = [d for d in payload["diagnostics"] if d["blocking"]]
    assert blocking
    for item in blocking:
        assert item.get("actions"), f"blocking diagnostic {item['code']} must carry actions"
        assert all("kind" in action for action in item["actions"])


# --- fleet-regression-fixtures / manifest ---------------------------------


def test_manifest_lists_all_four_capabilities() -> None:
    manifest = manifest_path(FIXTURES / "valid_manifest")
    capabilities = manifest["capabilities"]
    for cap in (
        "version-aware-keywords",
        "cross-artifact-graph",
        "code-actions",
        "fleet-regression-fixtures",
    ):
        assert cap in capabilities, f"missing capability: {cap}"
        assert capabilities[cap]["status"] == "available"
    # artifact roles are the generic fleet model, not MatMaster policy
    assert set(manifest["artifact_roles"]) == set(ALL_ROLES)
    assert manifest["preflight_envelope"] == "DiagnosticEnvelope/v1"


def test_manifest_without_path_still_describes_surface() -> None:
    manifest = manifest_path(None)
    assert set(manifest["codes"])
    assert manifest["capabilities"]["code-actions"]["blocking_gate"]


def test_manifest_merges_fixture_expectations() -> None:
    manifest = manifest_path(FIXTURES / "valid_manifest")
    fixtures = manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"]
    names = {item["name"] for item in fixtures}
    assert {
        "valid_manifest",
        "missing_model_potential",
        "task_param_mismatch",
        "suspicious_md_params",
        "model_engine_incompatible",
        "unresolved_training_config",
    } <= names


def test_fleet_manifest_helper_pure_data() -> None:
    manifest = fleet_manifest(fixtures=[{"name": "x", "expect_ok": True}])
    assert manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"] == [
        {"name": "x", "expect_ok": True}
    ]
    # every code entry is self-describing for the parent probe
    for body in manifest["codes"].values():
        assert body["severity"] in {"error", "warning", "information", "hint"}
        assert "capability" in body
        assert "summary" in body


def test_fixture_expectations_match_actual_preflight() -> None:
    """The fleet manifest's declared fixture expectations must match reality.

    This is the regression-evidence contract: the parent ``bohrium_skills``
    probe consumes the manifest and replays these fixtures, so the declared
    expectations have to agree with what the preflight actually emits.
    """
    manifest = manifest_path(FIXTURES / "valid_manifest")
    repo_root = Path(__file__).resolve().parent.parent
    for fixture in manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"]:
        payload = preflight_path(repo_root / fixture["path"])
        assert payload["ok"] is fixture["expect_ok"], (
            f"{fixture['name']}: manifest expects ok={fixture['expect_ok']}, got ok={payload['ok']}"
        )
        if fixture["expect_codes"]:
            assert set(fixture["expect_codes"]) <= _envelope_codes(payload), (
                f"{fixture['name']}: expected codes {fixture['expect_codes']}, "
                f"got {sorted(_envelope_codes(payload))}"
            )


# --- dedupe + workspace detection -----------------------------------------


def test_dedupe_preflight_drops_overlap_with_legacy() -> None:
    legacy = [{"code": "MLIP-E086", "severity": "warning", "message": "missing file"}]
    preflight = [
        {"code": CODE_MISSING_ARTIFACT, "severity": "error", "message": "missing"},
        {"code": CODE_TASK_PARAM_MISMATCH, "severity": "error", "message": "params"},
    ]
    result = _dedupe_preflight(legacy, preflight)
    codes = {item["code"] for item in result}
    assert CODE_MISSING_ARTIFACT not in codes  # suppressed (overlap with MLIP-E086)
    assert CODE_TASK_PARAM_MISMATCH in codes


def test_looks_like_workspace_requires_manifest(tmp_path: Path) -> None:
    assert _looks_like_workspace(tmp_path) is False
    (tmp_path / "manifest.json").write_text("{}", encoding="utf-8")
    assert _looks_like_workspace(tmp_path) is True


def test_check_on_single_manifest_file_does_not_run_preflight(tmp_path: Path) -> None:
    # A bare manifest file (not a workspace dir) must keep the legacy
    # single-file behavior and NOT flood with blocking preflight errors.
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"model": "x"}', encoding="utf-8")
    payload = check_path(manifest_path)
    preflight_codes = {
        CODE_MISSING_ARTIFACT,
        CODE_TASK_PARAM_MISMATCH,
        CODE_MISSING_REQUIRED_KEY,
    }
    assert not (_envelope_codes(payload) & preflight_codes)


def test_check_on_full_workspace_merges_preflight() -> None:
    payload = check_path(FIXTURES / "task_param_mismatch")
    codes = _envelope_codes(payload)
    assert CODE_TASK_PARAM_MISMATCH in codes
    assert payload["diagnostic_envelope"] == "v1"


def test_find_manifest_prefers_named_manifest(tmp_path: Path) -> None:
    (tmp_path / "other.json").write_text("{}", encoding="utf-8")
    assert find_manifest(tmp_path).name == "other.json"
    (tmp_path / "manifest.json").write_text("{}", encoding="utf-8")
    assert find_manifest(tmp_path).name == "manifest.json"


def test_artifact_graph_is_json_serializable_for_fleet_report() -> None:
    payload = preflight_path(FIXTURES / "valid_manifest")
    # artifacts must round-trip through json.dumps cleanly for the parent probe
    serialized = json.dumps(payload["artifacts"], sort_keys=True)
    assert "primary-input" in serialized
    assert "structure" in serialized


def test_artifact_graph_class_smoke() -> None:
    graph = ArtifactGraph(case_dir=Path("/tmp"))
    assert graph.nodes == []
    assert graph.by_role("structure") == []
    assert graph.to_json() == []
