# Diagnostic Engine v1

MLIP diagnostics use `DiagnosticEnvelope/v1` with `error`, `warning`, `information`, and `hint` severities. Blocking behavior is controlled by `lsp-capabilities.json`, not by OpenQC guesswork.

## Raw evidence

- `raw/assets/diagnostic_codes.py` — diagnostic code registry extracted from source
- `raw/assets/manifest.json` — provenance manifest with checksums
- `src/mlip_lsp/rich_diagnostics.py` — DiagnosticEnvelope/v1 serialization
