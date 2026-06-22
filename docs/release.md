# Release Checklist

Use this checklist before tagging a release.

## Local Validation

```bash
python -m unittest discover -s tests
ruff check .
python -m build
python -m tracebench.cli --version
python -m tracebench.cli doctor --trace-file examples/traces/baseline.jsonl
python -m tracebench.cli validate examples/traces/baseline.jsonl
python -m tracebench.cli summarize examples/traces/baseline.jsonl --format markdown
docker build -t agent-tracebench:dev .
```

## Repository Checks

- Confirm example traces are synthetic and do not contain private data.
- Confirm the changelog includes the release date and user-facing changes.
- Confirm `README.md`, `docs/cli.md`, and `docs/trace-schema.md` match the CLI.
- Confirm generated artifacts such as `build/`, `dist/`, and `*.egg-info/` are
  not committed.
- Confirm the release-artifact workflow builds and validates `dist/*` on tag
  pushes and manual workflow runs.
