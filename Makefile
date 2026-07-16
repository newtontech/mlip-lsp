.PHONY: install format lint typecheck test wiki-check verify-release build smoke-wheel check cleanup-merged

PYTHON ?= python

install:
	bash scripts/install.sh

format:
	$(PYTHON) -m ruff format src tests scripts/verify_release.py
	$(PYTHON) -m ruff check --fix src tests scripts/verify_release.py

lint:
	$(PYTHON) -m ruff check src tests scripts/verify_release.py

typecheck:
	$(PYTHON) -m mypy src scripts/verify_release.py

test:
	$(PYTHON) -m pytest

wiki-check:
	bash scripts/check-llm-wiki.sh

verify-release:
	$(PYTHON) scripts/verify_release.py --tag v$$(cat VERSION)

build:
	rm -rf build dist
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*

smoke-wheel: build
	bash scripts/smoke_wheel.sh dist/*.whl

check: lint typecheck test wiki-check verify-release

cleanup-merged:
	bash scripts/cleanup_merged_worktrees.sh
