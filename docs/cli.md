# CLI Reference

Agent TraceBench installs a `tracebench` command.

## Doctor

```bash
tracebench doctor
tracebench doctor --trace-file examples/traces/baseline.jsonl --format json
```

Checks schema availability and, when a trace is provided, validates the JSONL
trace. Returns exit code `1` if a check fails.

## Schema

```bash
tracebench schema --format json
tracebench schema --format markdown
```

Prints the trace-step schema for local tooling or documentation.

## Validate

```bash
tracebench validate examples/traces/baseline.jsonl
tracebench validate examples/traces/baseline.jsonl --format json
```

Returns exit code `0` for valid traces and `1` for malformed traces.

## Summarize

```bash
tracebench summarize examples/traces/baseline.jsonl
tracebench summarize examples/traces/baseline.jsonl --format markdown
```

Reports step count, total latency, p95 step latency, token totals, and failed
steps.

## Replay

```bash
tracebench replay examples/traces/baseline.jsonl
```

Emits steps ordered by start time with offsets from the first step.

## OpenTelemetry Export

```bash
tracebench otel examples/traces/baseline.jsonl
```

Writes OpenTelemetry-compatible span JSON with stable generated IDs when trace
IDs or span IDs are not present in the input.

## Compare

```bash
tracebench compare examples/traces/baseline.jsonl examples/traces/candidate.jsonl
tracebench compare examples/traces/baseline.jsonl examples/traces/candidate.jsonl --format markdown
```

Returns exit code `0` when the candidate stays within configured latency, token,
and failure thresholds. Returns exit code `2` when a regression is detected.

## Cost, Outliers, and Redaction

```bash
tracebench cost examples/traces/baseline.jsonl --input-cost-per-million 1 --output-cost-per-million 3
tracebench outliers examples/traces/baseline.jsonl --threshold-ms 250
tracebench redact examples/traces/baseline.jsonl --output redacted.jsonl
```

Use redaction before sharing traces outside a trusted environment.
