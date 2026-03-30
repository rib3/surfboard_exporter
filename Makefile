.PHONY: http http-dev

http:
	python main.py

http-dev:
	watchmedo auto-restart --patterns="*.py;pyproject.toml" --recursive -- $(MAKE) http
