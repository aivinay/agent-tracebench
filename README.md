# Agent TraceBench

OpenTelemetry-native trace inspection for LLM applications and agent workflows.

[![CI](https://github.com/aivinay/agent-tracebench/actions/workflows/ci.yml/badge.svg)](https://github.com/aivinay/agent-tracebench/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Agent TraceBench is a small command-line workbench for JSONL traces. It turns
agent steps into summaries, replay events, regression checks, cost estimates,
latency outlier reports, redacted exports, and OpenTelemetry-compatible span
JSON.

Use it when you want trace behavior to be visible in local development and CI
without standing up a full tracing backend for every experiment.

## Start With a Trace

Each line is one step:

```jsonl
{"name":"plan","started_at_ms":0,"ended_at_ms":120,"prompt_tokens":200,"completion_tokens":50}
{"name":"tool.search","started_at_ms":125,"ended_at_ms":420,"prompt_tokens":80,"completion_tokens":30}
{"name":"final","started_at_ms":430,"ended_at_ms":520,"prompt_tokens":40,"completion_tokens":80}
```

Then inspect it:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

tracebench doctor --trace-file examples/traces/baseline.jsonl
tracebench validate examples/traces/baseline.jsonl
tracebench summarize examples/traces/baseline.jsonl --format markdown
```

## What You Can Ask

| Question | Command |
| --- | --- |
| Is this trace valid? | `tracebench validate trace.jsonl` |
| What happened overall? | `tracebench summarize trace.jsonl` |
| What order did steps run in? | `tracebench replay trace.jsonl` |
| Did this candidate regress? | `tracebench compare baseline.jsonl candidate.jsonl` |
| What would this cost? | `tracebench cost trace.jsonl --input-cost-per-million 1 --output-cost-per-million 3` |
| Which steps are slow? | `tracebench outliers trace.jsonl --threshold-ms 500` |
| Can I share a scrubbed trace? | `tracebench redact trace.jsonl --output redacted.jsonl` |
| Can this feed observability tooling? | `tracebench otel trace.jsonl` |

`tracebench compare` returns exit code `2` when the candidate exceeds configured
latency, token, or failure thresholds, making it useful in pull requests.

## Trace Contract

Required fields:

- `name`
- `started_at_ms`
- `ended_at_ms`

Optional fields:

- `prompt_tokens`
- `completion_tokens`
- `status`
- `error_type`
- `attributes`
- `trace_id`, `span_id`, `parent_span_id`

Print the full schema:

```bash
tracebench schema --format markdown
tracebench schema --format json
```

See [docs/trace-schema.md](docs/trace-schema.md).

## From Local Debugging to CI

A typical regression check looks like this:

```bash
tracebench compare \
  examples/traces/baseline.jsonl \
  examples/traces/candidate.jsonl \
  --max-latency-regression-pct 10 \
  --max-token-regression-pct 10 \
  --format markdown
```

For observability integration, export OpenTelemetry-compatible span JSON:

```bash
tracebench otel examples/traces/baseline.jsonl
```

Generated trace and span IDs are stable when explicit IDs are not supplied.

## Privacy Notes

Agent traces can contain prompts, completions, tool arguments, URLs, and other
sensitive operational data. Redaction is key-based and recursive for nested
objects:

```bash
tracebench redact examples/traces/baseline.jsonl --output redacted.jsonl
```

Agent TraceBench does not send telemetry, call model providers, or store traces
unless you explicitly write output files.

## Validation and Release Surface

The project includes unit tests, linting, build checks, CLI smoke tests, a
Dockerfile, and a release-artifact workflow.

```bash
python -m unittest discover -s tests
ruff check .
python -m build
tracebench doctor --trace-file examples/traces/baseline.jsonl
tracebench compare examples/traces/baseline.jsonl examples/traces/baseline.jsonl
```

Container smoke:

```bash
docker build -t agent-tracebench:dev .
docker run --rm agent-tracebench:dev --version
```

## Documentation

- [CLI reference](docs/cli.md)
- [Trace schema](docs/trace-schema.md)
- [Architecture](docs/architecture.md)
- [Reproducibility](docs/reproducibility.md)
- [Validation notes](docs/validation.md)
- [Release checklist](docs/release.md)
- [Roadmap](docs/roadmap.md)

## Development

```bash
make install
make check
```

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md)
and [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Vinay Gupta
