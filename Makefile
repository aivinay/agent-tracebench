PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_RUFF := $(VENV)/bin/ruff

.PHONY: install test lint build smoke check docker clean

install:
	$(PYTHON) -m venv --clear $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e ".[dev]"

test:
	PYTHONPATH=src $(VENV_PYTHON) -m unittest discover -s tests

lint:
	$(VENV_RUFF) check .

build:
	$(VENV_PYTHON) -m build

smoke:
	PYTHONPATH=src $(VENV_PYTHON) -m tracebench.cli --version
	PYTHONPATH=src $(VENV_PYTHON) -m tracebench.cli doctor --trace-file examples/traces/baseline.jsonl
	PYTHONPATH=src $(VENV_PYTHON) -m tracebench.cli schema --format markdown
	PYTHONPATH=src $(VENV_PYTHON) -m tracebench.cli validate examples/traces/baseline.jsonl
	PYTHONPATH=src $(VENV_PYTHON) -m tracebench.cli summarize examples/traces/baseline.jsonl --format markdown

check: lint test build smoke

docker:
	docker build -t agent-tracebench:dev .

clean:
	rm -rf .pytest_cache .ruff_cache build dist src/*.egg-info
