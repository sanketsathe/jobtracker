.PHONY: check test test-fast

PYTHON ?= $(if $(wildcard ./.venv/bin/python),./.venv/bin/python,python3)

check:
	$(PYTHON) manage.py check

test:
	$(PYTHON) manage.py test

test-fast:
	$(PYTHON) manage.py test tracker
