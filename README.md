<h1 align="center">Agent TraceBench</h1>

<p align="center"><strong>OpenTelemetry-native observability and replay tools for LLM applications and agents.</strong></p>

<p align="center">
  <a href="https://github.com/aivinay/agent-tracebench/actions/workflows/ci.yml"><img src="https://github.com/aivinay/agent-tracebench/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
</p>

<p align="center">
  <a href="#get-started">Install</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#proof">Proof</a> ·
  <a href="#privacy-and-scope">Privacy</a> ·
  <a href="docs/">Docs</a>
</p>

---

> Agent TraceBench turns lightweight JSONL traces into deterministic summaries,
> replay events, regression checks, redacted exports, and
> OpenTelemetry-compatible span JSON.

It is built for teams that need agent behavior to be inspectable in local
development, CI, and production observability workflows without requiring a full
tracing backend for every experiment.

## What It Does

- Models agent execution as ordered trace steps.
- Reads, writes, and validates JSONL trace files.
- Summarizes latency, p95 step latency, token usage, and failed steps.
- Clusters failures by stable error type.
- Emits replay events in causal order.
- Exports OpenTelemetry-compatible span JSON.
- Compares baseline and candidate traces for CI regression checks.
- Estimates token cost, detects latency outliers, and redacts sensitive fields.
- Prints schema and report output as JSON or Markdown.
- Provides `doctor` diagnostics for local setup and example traces.

## How It Works

```text
JSONL trace steps
  |
  v
Schema validation
  |
  v
Trace model: latency, token counts, status, attributes
  |
  v
Analysis: summary, failures, replay, cost, outliers
  |
  v
Comparison: baseline vs candidate thresholds
  |
  v
Reports: JSON, Markdown, OpenTelemetry-compatible span JSON
```

The core invariant: trace analysis is deterministic and suitable for CI, so the
same trace inputs produce the same metrics, reports, and exit codes.

## Get Started

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

```bash
tracebench --version
tracebench doctor --trace-file examples/traces/baseline.jsonl
tracebench schema --format markdown
tracebench validate examples/traces/baseline.jsonl
tracebench summarize examples/traces/baseline.jsonl --format markdown
tracebench compare examples/traces/baseline.jsonl examples/traces/candidate.jsonl --format markdown
```

Additional analysis commands:

```bash
tracebench replay examples/traces/baseline.jsonl
tracebench otel examples/traces/baseline.jsonl
tracebench cost examples/traces/baseline.jsonl --input-cost-per-million 1.0 --output-cost-per-million 3.0
tracebench outliers examples/traces/baseline.jsonl --median-multiplier 1.5
tracebench redact examples/traces/baseline.jsonl --output redacted.jsonl
```

Container smoke check:

```bash
docker build -t agent-tracebench:dev .
docker run --rm agent-tracebench:dev --version
```

## Proof

The current release is validated with unit tests, linting, package build checks,
CLI smoke checks, trace validation, and a release-artifact workflow.

```bash
python -m unittest discover -s tests
ruff check .
python -m build
tracebench doctor --trace-file examples/traces/baseline.jsonl
tracebench compare examples/traces/baseline.jsonl examples/traces/baseline.jsonl
```

Validation covers summary metrics, failure clustering, replay ordering, invalid
input diagnostics, JSONL round-trips, OpenTelemetry-compatible export,
regression comparison, cost estimation, outlier detection, redaction, schema
output, diagnostics, and CLI commands. See [docs/validation.md](docs/validation.md).

## Trace Schema

Each JSONL row represents one agent step:

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

Print the canonical schema with:

```bash
tracebench schema --format json
```

## Privacy and Scope

Agent traces can contain prompts, completions, tool arguments, URLs, and other
sensitive operational data. Use `tracebench redact` before sharing traces outside
a trusted environment.

Agent TraceBench does not send telemetry, call model providers, or store traces
unless you explicitly write output files. It is a local trace-analysis toolkit,
not a tracing backend, agent framework, or model evaluation platform.

## Documentation

| Start here | Go deeper |
| --- | --- |
| [CLI reference](docs/cli.md) | [Trace schema](docs/trace-schema.md) |
| [Architecture](docs/architecture.md) | [Reproducibility](docs/reproducibility.md) |
| [Validation notes](docs/validation.md) | [Release checklist](docs/release.md) |
| [Roadmap](docs/roadmap.md) | [Contributing](CONTRIBUTING.md) |

## Development

```bash
make install
make check
```

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md)
and [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Vinay Gupta
