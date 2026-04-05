.PHONY: http http-dev lint lint-fix

http:
	python main.py

http-dev:
	watchmedo auto-restart --patterns="*.py;pyproject.toml" --recursive -- $(MAKE) http

lint:
	ruff format --diff
	ruff check # --diff excludes unfixable violations
	ruff check --diff
	isort --diff .
	black --diff .

lint-fix:
	ruff format # address formatting errors (Line too long) before they error under check (--fix does not address them)
	ruff check --fix
	isort .
	black .
