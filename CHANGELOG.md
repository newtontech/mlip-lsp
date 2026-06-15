# Changelog

All notable changes to mlip-lsp are documented in this file.

## [Unreleased]

### Added

- `raw/assets/manifest.json` provenance manifest with retrieval dates, software versions, and SHA-256 checksums (#34).
- `VERSION` file aligned with package metadata for family-gate provenance checks.
- `tests/test_provenance_manifest.py` for manifest checksum and capability contract validation.

### Changed

- `lsp-capabilities.json` adds `provenanceManifest`, `diagnostic_coverage`, and corrected `fixturePaths`/`outputLogPatterns`.

## [0.2.0] - 2026-06-13

### Added

- Closed-loop fixture tests and DiagnosticEnvelope/v1 CLI envelope coverage (#37).
- LLM wiki raw collection and grounded LSP capabilities (#32).

## [0.1.0] - 2026-06-12

### Added

- Initial MLIP LSP with manifest diagnostics, ASE script checks, and agent CLI.
