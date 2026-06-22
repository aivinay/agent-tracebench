# Examples

The `examples/traces` directory contains small synthetic traces that exercise
the main CLI workflow.

```bash
tracebench validate examples/traces/baseline.jsonl
tracebench summarize examples/traces/baseline.jsonl --format markdown
tracebench compare examples/traces/baseline.jsonl examples/traces/candidate.jsonl --format markdown
tracebench otel examples/traces/baseline.jsonl
```

Example traces are intentionally synthetic. Do not commit real prompts,
completions, user records, credentials, or private operational data.
