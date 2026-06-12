# OpenQC Agent Context

OpenQC consumes `mlip-lsp-tool` and `lsp-capabilities.json` to assemble diagnostics, hover, completion, symbols, examples, next-token guidance, and repair-plan hints for `mlip` documents.

## Wiki-grounded surfaces

| LSP operation | Wiki evidence | Raw evidence |
|---------------|---------------|--------------|
| `check` / diagnostics | [Diagnostic Codes Reference](Diagnostic_Codes_Reference.md), [Diagnostic System](../concepts/Diagnostic_System.md) | `raw/assets/diagnostic_codes.py`, `src/mlip_lsp/features/rules.py` |
| `hover` | [MLIP Manifest](../entities/MLIP_Manifest.md), [MLIP Task Types](../entities/MLIP_Task_Types.md), [MLIP Models](../entities/MLIP_Models.md) | `raw/assets/valid_manifest.json` |
| `complete` | [Input Format Reference](Input_Format_Reference.md) | manifest keys: `model`, `structure`, `task`, `parameters` |
| `context` | [MatMaster Execution Contract](../concepts/MatMaster_Execution_Contract.md) | `raw/assets/matmaster_rules.py` |
| `symbols` | [ASE Atomistic Simulation](../entities/ASE_Atomistic_Simulation.md) | `raw/assets/valid_ase_script.py` |
| `fix` | Diagnostic fix hints (MLIP-E080–E087, MLIP-W080) | `tests/fixtures/invalid_*.json` |

## Upstream manuals

Official MLIP ecosystem documentation is indexed in `raw/assets/upstream-sources.md` (MTP, NEP, MACE, DeePMD-kit, NequIP, MatMaster rules).

## Example manifests

- Minimal optimize: `raw/assets/valid_manifest.json`
- MD with parameters: `raw/assets/examples/manifest_md.json`

See [Typical Workflows](Typical_Workflows.md) for `mlip-lint`, `mlip-fmt`, and `mlip-lsp --stdio` usage.
