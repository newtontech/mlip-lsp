.PHONY: install format lint typecheck test check cleanup-merged

install:
	bash scripts/install.sh

format:
	bash scripts/format.sh

lint:
	bash scripts/lint.sh

typecheck:
	bash scripts/typecheck.sh

test:
	bash scripts/test.sh

wiki-check:
	bash scripts/check-llm-wiki.sh

check: lint typecheck test wiki-check

cleanup-merged:
	bash scripts/cleanup_merged_worktrees.sh
