# Trace Schema

Agent TraceBench uses newline-delimited JSON. Each row is one agent step.

Print the current schema with:

```bash
tracebench schema --format markdown
```

| Field | Required | Description |
| --- | --- | --- |
| `name` | yes | Step, tool, model call, or operation name |
| `started_at_ms` | yes | Millisecond timestamp or relative offset |
| `ended_at_ms` | yes | Millisecond timestamp or relative offset |
| `prompt_tokens` | no | Input token count |
| `completion_tokens` | no | Output token count |
| `status` | no | `ok` or `error` |
| `error_type` | no | Stable failure cluster label |
| `attributes` | no | Additional structured metadata |
| `trace_id` | no | Optional trace identifier |
| `span_id` | no | Optional span identifier |
| `parent_span_id` | no | Optional parent span identifier |

## Privacy

Traces may contain sensitive prompts, completions, tool arguments, and
credentials. Use:

```bash
tracebench redact trace.jsonl --output redacted.jsonl
```

Default redaction covers common keys such as `prompt`, `completion`, `messages`,
`input`, `output`, `api_key`, `token`, `secret`, and `password`.

## Validation Rules

- `name`, `started_at_ms`, and `ended_at_ms` are required.
- Timestamps and token counts must be non-negative integers.
- `ended_at_ms` must be greater than or equal to `started_at_ms`.
- `status` must be `ok` or `error`.
- `attributes` must be a JSON object when present.

Run:

```bash
tracebench validate trace.jsonl --format json
```
