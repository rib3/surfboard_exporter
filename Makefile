.PHONY: http
http:
	PYTHONPATH=src python -m surfboard_exporter $(ARGS)

.PHONY: http-dev
http-dev:
	watchmedo auto-restart --patterns="*.py;pyproject.toml" --recursive -- $(MAKE) http ARGS="$(ARGS)"

.PHONY: lint
lint:
	ruff format --diff
	ruff check # --diff excludes unfixable violations
	ruff check --diff
	isort --diff .

.PHONY: lint-fix
lint-fix:
	ruff format # address formatting errors (Line too long) before they error under check (--fix does not address them)
	ruff check --fix
	isort .
