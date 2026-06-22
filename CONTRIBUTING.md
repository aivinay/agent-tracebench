# Contributing

Thank you for considering a contribution to Agent TraceBench.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m unittest discover -s tests
ruff check .
```

## Contribution guidelines

- Keep trace schemas stable and documented.
- Add tests for new metrics, exporters, and regression checks.
- Prefer deterministic outputs so traces can be used in CI.
- Avoid storing prompts, secrets, or user data in example traces.
