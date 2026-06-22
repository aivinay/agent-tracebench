# Reproducibility

Agent TraceBench produces deterministic analysis for the same JSONL inputs and
thresholds.

## Recommended Python

- Python 3.10
- Python 3.11
- Python 3.12

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Equivalent repo command:

```bash
make install
```

## Validation

```bash
python -m unittest discover -s tests
ruff check .
python -m build
tracebench doctor --trace-file examples/traces/baseline.jsonl
tracebench compare examples/traces/baseline.jsonl examples/traces/baseline.jsonl
```

## Determinism Contract

- JSONL rows are parsed in file order.
- Replay events are sorted by start time and name.
- Generated span IDs derive from stable trace content.
- Comparison exit codes depend only on summaries and configured thresholds.
- Redaction is key-based and recursive for nested objects.

## CI Scope

GitHub Actions runs tests, linting, package build checks, and CLI smoke checks on
Python 3.10, 3.11, and 3.12.

## Release Artifacts

Tag builds and manual workflow runs build the source distribution and wheel,
validate them with `twine check`, and upload the distribution files as workflow
artifacts.
