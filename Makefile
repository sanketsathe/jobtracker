.PHONY: check test test-fast

PYTHON ?= python3

check:
	$(PYTHON) manage.py check

test:
	$(PYTHON) manage.py test

test-fast:
	$(PYTHON) manage.py test tracker
