.PHONY: install test lint build smoke clean

install:
	python -m pip install -e ".[dev]"

test:
	PYTHONPATH=src python -m unittest discover -s tests

lint:
	ruff check .

build:
	python -m build

smoke:
	PYTHONPATH=src python -m tracebench.cli --version
	PYTHONPATH=src python -m tracebench.cli schema --format markdown
	PYTHONPATH=src python -m tracebench.cli validate examples/traces/baseline.jsonl
	PYTHONPATH=src python -m tracebench.cli summarize examples/traces/baseline.jsonl --format markdown

clean:
	rm -rf .pytest_cache .ruff_cache build dist src/*.egg-info
