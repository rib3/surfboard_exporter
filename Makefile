.PHONY: http http-dev lint lint-fix

http:
	python main.py

http-dev:
	watchmedo auto-restart --patterns="*.py;pyproject.toml" --recursive -- $(MAKE) http

lint:
	ruff check --diff
	isort --diff .
	black --diff .

lint-fix:
	ruff check --fix
	isort .
	black .
