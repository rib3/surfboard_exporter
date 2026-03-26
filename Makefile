.PHONY: http http-dev

http:
	python main.py

http-dev:
	watchmedo auto-restart --patterns="*.py" --recursive -- $(MAKE) http
