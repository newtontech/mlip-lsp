# MLIP upstream source manifest

Concise index of official documentation used by the LLM wiki and LSP hover/diagnostics.

| Label | Kind | URL | Local digest |
|-------|------|-----|--------------|
| MLIP portal | official_docs | https://mlip.skoltech.ru/ | `raw/assets/mlip-readme.md` |
| MLIP-2 / MTP | official_docs | https://gitlab.com/ashapeev/mlip-2 | `raw/assets/mtp-documentation.md` |
| GPUMD / NEP | official_docs | https://gpumd.org/ | `raw/assets/nep_config.txt`, `wiki/entities/NEP_Configuration.md` |
| MACE | official_examples | https://github.com/acesuit/mace | `raw/assets/mlip-examples.md` |
| DeePMD-kit | official_examples | https://github.com/deepmodeling/deepmd-kit | `raw/assets/mlip-input-format.md` |
| NequIP / Allegro | official_examples | https://github.com/mir-group/nequip | `raw/assets/mlip-readme.md` |
| MatMaster contract | repo_rules | `raw/assets/matmaster_rules.py` | `wiki/concepts/MatMaster_Execution_Contract.md` |
| Diagnostic codes | repo_rules | `raw/assets/diagnostic_codes.py` | `wiki/synthesis/Diagnostic_Codes_Reference.md` |

## Example inputs in this repo

- `raw/assets/valid_manifest.json` — minimal MatMaster manifest (optimize task)
- `raw/assets/examples/manifest_md.json` — manifest with MD parameters (from MatMaster patterns)
- `raw/assets/valid_ase_script.py` — ASE + MLIP driver script
- `raw/assets/nep_config.txt` — NEP training configuration excerpt

## Wiki cross-links

- Manifest schema: `wiki/entities/MLIP_Manifest.md`
- Agent context: `wiki/synthesis/openqc-agent-context.md`
- Diagnostic engine: `wiki/concepts/diagnostic-engine-v1.md`

Machine-readable provenance with checksums lives in `raw/assets/manifest.json`
(`provenance-manifest-v1`). Update checksums when replacing raw digests.
