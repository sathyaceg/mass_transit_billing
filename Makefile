PYTHON := .venv/bin/python3

.PHONY: setup format lint test check

setup:
	$(PYTHON) -m pip install -e ".[dev]"

format:
	$(PYTHON) -m autopep8 --in-place --recursive --aggressive --aggressive --max-line-length 88 src tests
	$(PYTHON) -m ruff check --fix src tests

lint:
	$(PYTHON) -m ruff check src tests

test:
	$(PYTHON) -m pytest

check: format lint test
