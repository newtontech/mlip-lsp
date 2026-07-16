# mlip-lsp

`mlip-lsp` is an MVP Language Server Protocol and CLI toolkit for MLIP files used in MatMaster workflows.

Current release: `0.2.1`

The first version is intentionally deterministic and lightweight: static parsing, lint diagnostics, safe formatting, and machine-readable JSON output live here. Full scientific execution, Bohrium submission, and heavy workflow automation stay outside the LSP and should be invoked explicitly by higher-level tools.

## CLI Surface

```bash
mlip-lsp --stdio
mlip-lint ./case --json
mlip-fmt -w input.file
mlip-test static ./case --json
```

Diagnostic JSON uses the shared newtontech LSP shape: `file`, `line`, `column`, `severity`, `code`, `message`, `evidence`, `suggested_fix`, and `confidence`.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
ruff check src tests
ruff format --check src tests
mypy src
```

## Releases

Releases use PyPI Trusted Publishing and GitHub Releases. A pushed `v*` tag
starts the release workflow, which verifies that the tag matches all source
metadata, builds and checks the distributions, and installs the wheel into a
fresh virtual environment for server, agent CLI, valid/invalid input, and
runtime-log smoke tests. Only the protected `pypi` environment receives
`id-token: write`; no long-lived PyPI credential is stored.

After this PR is merged and its release point is approved, create `v0.2.1` on
the merge commit. Pull requests and ordinary branch pushes cannot publish.

## Scope

This repository is seeded from MatMaster skill contracts and evaluation fixtures. The roadmap is tracked in GitHub issues and should converge toward parser-backed diagnostics, completion, hover documentation, formatting, OpenQC integration, and regression fixtures.
