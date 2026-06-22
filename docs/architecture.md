# Architecture

Agent TraceBench is a local trace-analysis toolkit for JSONL agent execution
traces. It keeps the trace format simple while producing deterministic metrics,
reports, and comparison exit codes.

## Core Flow

```text
JSONL trace file
  |
  v
Line parser and validator
  |
  v
AgentStep model
  |
  v
Summary, replay, cost, outlier, and failure analysis
  |
  v
Baseline/candidate comparison
  |
  v
JSON / Markdown / OpenTelemetry-compatible output
```

## Layers

- `models.py`: defines the trace-step schema, validation, and serialization.
- `io.py`: reads, writes, and validates JSONL traces with line-level issues.
- `bench.py`: summarizes traces, clusters failures, and emits replay events.
- `analysis.py`: estimates token cost, detects latency outliers, and redacts
  sensitive attributes.
- `assertions.py`: compares baseline and candidate traces with regression
  thresholds.
- `otel.py`: converts trace steps to OpenTelemetry-compatible span JSON.
- `schema.py`: exposes the trace schema as JSON and Markdown.
- `reports.py`: renders comparison and validation reports.
- `doctor.py`: checks schema availability and optional trace validity.

## Boundaries

Agent TraceBench does not call model providers, run agents, start a collector, or
store traces outside caller-provided output files. It is designed to sit between
agent runtimes and observability systems.
