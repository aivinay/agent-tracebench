# Agent TraceBench

[![CI](https://github.com/aivinay/agent-tracebench/actions/workflows/ci.yml/badge.svg)](https://github.com/aivinay/agent-tracebench/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

OpenTelemetry-native observability and replay framework for LLM applications and agents.

Agent TraceBench turns lightweight JSONL traces into deterministic summaries,
regression checks, replay events, redacted exports, and OpenTelemetry-compatible
span JSON. It is designed for teams that need agent behavior to be inspectable in
local development, CI, and production observability workflows.

## Features

- Model agent execution as ordered trace steps.
- Read and write JSONL trace files.
- Validate trace files with line-level diagnostics.
- Summarize total latency, p95 step latency, token usage, and failed steps.
- Cluster failures by error type for quick triage.
- Emit replay events that preserve causal ordering.
- Export OpenTelemetry-compatible span JSON for observability pipelines.
- Compare baseline and candidate traces for CI regression checks.
- Estimate token cost from configurable per-million token rates.
- Detect latency outliers and redact sensitive trace attributes before sharing.
- Print schema and report output as JSON or Markdown.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python3 -m unittest discover -s tests
```

Create a JSONL trace file:

```jsonl
{"name":"plan","started_at_ms":0,"ended_at_ms":120,"prompt_tokens":200,"completion_tokens":50}
{"name":"tool.search","started_at_ms":125,"ended_at_ms":420,"prompt_tokens":80,"completion_tokens":30}
```

Then summarize it:

```bash
tracebench --version
tracebench schema --format markdown
tracebench validate examples/traces/baseline.jsonl
tracebench summarize examples/traces/baseline.jsonl --format markdown
tracebench replay examples/traces/baseline.jsonl
tracebench otel examples/traces/baseline.jsonl
tracebench compare examples/traces/baseline.jsonl examples/traces/candidate.jsonl --format markdown
tracebench cost examples/traces/baseline.jsonl --input-cost-per-million 1.0 --output-cost-per-million 3.0
tracebench outliers examples/traces/baseline.jsonl --median-multiplier 1.5
tracebench redact examples/traces/baseline.jsonl --output redacted.jsonl
```

`tracebench compare` exits with status code `2` when latency, token, or failure
regressions exceed configured thresholds. This makes trace behavior testable in
pull requests without requiring a production tracing backend.

Use `tracebench redact` before sharing traces outside a trusted environment.
Default redaction covers common prompt, completion, credential, token, and
message attribute keys.

## Trace schema

Each JSONL row represents one agent step. The command below prints the canonical
schema:

```bash
tracebench schema --format json
```

| Field | Required | Description |
| --- | --- | --- |
| `name` | yes | Step, tool, model call, or application operation name |
| `started_at_ms` | yes | Millisecond timestamp or relative offset |
| `ended_at_ms` | yes | Millisecond timestamp or relative offset |
| `prompt_tokens` | no | Input token count |
| `completion_tokens` | no | Output token count |
| `status` | no | `ok` or `error` |
| `error_type` | no | Stable error cluster label |
| `attributes` | no | Additional structured metadata |
| `trace_id`, `span_id`, `parent_span_id` | no | Optional tracing identifiers |

## Documentation

- [Trace schema](docs/trace-schema.md)
- [CLI reference](docs/cli.md)
- [Validation notes](docs/validation.md)
- [Release checklist](docs/release.md)
- [Roadmap](docs/roadmap.md)

## Development

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests
ruff check .
python -m build
```

## Roadmap

Agent TraceBench is designed to grow toward:

- Direct OpenTelemetry SDK exporters.
- Trace replay for agent debugging and regression tests.
- Token, cost, and latency attribution across nested agent steps.
- Additional evaluation hooks for model, prompt, and tool changes.
- Failure clustering for common agent reliability issues.

See [docs/roadmap.md](docs/roadmap.md) for the initial milestones.
