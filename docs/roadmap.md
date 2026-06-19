# Roadmap

## Milestone 1: Trace Core

- Define a stable trace-step schema.
- Add JSONL import/export.
- Compute latency, token, and failure summaries.
- Provide replay events for deterministic inspection.

## Milestone 2: OpenTelemetry Integration

- Convert trace steps to spans.
- Add GenAI-oriented span attributes.
- Export traces through the OpenTelemetry SDK.
- Document local collector setup.

## Milestone 3: Evaluation Hooks

- Attach assertions to replayed traces.
- Compare traces across model or prompt changes.
- Generate CI-friendly regression reports.

## Milestone 4: Failure Clustering

- Group failures by error type, step, and tool.
- Add latency outlier detection.
- Produce actionable summaries for agent reliability debugging.
