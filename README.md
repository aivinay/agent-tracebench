# Agent TraceBench

OpenTelemetry-native observability and replay framework for LLM applications and agents.

Agent TraceBench starts as a small, testable toolkit for reasoning about agent execution traces: step latency, token usage, failures, replay order, and evaluation hooks. The long-term goal is to make agent behavior inspectable with the same rigor expected from production distributed systems.

## Current scope

- Model agent execution as ordered trace steps.
- Summarize total latency, p95 step latency, token usage, and failed steps.
- Cluster failures by error type for quick triage.
- Emit replay events that preserve causal ordering.
- Provide a small CLI for summarizing JSONL trace files.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests
```

Create a JSONL trace file:

```jsonl
{"name":"plan","started_at_ms":0,"ended_at_ms":120,"prompt_tokens":200,"completion_tokens":50}
{"name":"tool.search","started_at_ms":125,"ended_at_ms":420,"prompt_tokens":80,"completion_tokens":30}
```

Then summarize it:

```bash
tracebench summarize trace.jsonl
```

## Project direction

Agent TraceBench is designed to grow toward:

- OpenTelemetry spans and semantic conventions for GenAI workloads.
- Trace replay for agent debugging and regression tests.
- Token, cost, and latency attribution across nested agent steps.
- Evaluation hooks that compare behavior across model, prompt, and tool changes.
- Failure clustering for common agent reliability issues.

See [docs/roadmap.md](docs/roadmap.md) for the initial milestones.
