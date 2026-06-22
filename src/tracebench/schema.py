from __future__ import annotations

TRACE_FIELDS: tuple[dict[str, object], ...] = (
    {
        "name": "name",
        "required": True,
        "type": "string",
        "description": "Step, tool, model call, or application operation name.",
    },
    {
        "name": "started_at_ms",
        "required": True,
        "type": "integer",
        "description": "Millisecond timestamp or relative offset for step start.",
    },
    {
        "name": "ended_at_ms",
        "required": True,
        "type": "integer",
        "description": "Millisecond timestamp or relative offset for step end.",
    },
    {
        "name": "prompt_tokens",
        "required": False,
        "type": "integer",
        "description": "Input token count. Defaults to 0.",
    },
    {
        "name": "completion_tokens",
        "required": False,
        "type": "integer",
        "description": "Output token count. Defaults to 0.",
    },
    {
        "name": "status",
        "required": False,
        "type": "string",
        "description": "Step status: ok or error. Defaults to ok.",
    },
    {
        "name": "error_type",
        "required": False,
        "type": "string",
        "description": "Stable failure cluster label when status is error.",
    },
    {
        "name": "attributes",
        "required": False,
        "type": "object",
        "description": "Additional structured metadata for reports and span export.",
    },
    {
        "name": "trace_id",
        "required": False,
        "type": "string",
        "description": "Optional trace identifier used during span export.",
    },
    {
        "name": "span_id",
        "required": False,
        "type": "string",
        "description": "Optional span identifier used during span export.",
    },
    {
        "name": "parent_span_id",
        "required": False,
        "type": "string",
        "description": "Optional parent span identifier used during span export.",
    },
)


TRACE_JSON_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Agent TraceBench Trace Step",
    "type": "object",
    "required": ["name", "started_at_ms", "ended_at_ms"],
    "additionalProperties": True,
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "started_at_ms": {"type": "integer", "minimum": 0},
        "ended_at_ms": {"type": "integer", "minimum": 0},
        "prompt_tokens": {"type": "integer", "minimum": 0, "default": 0},
        "completion_tokens": {"type": "integer", "minimum": 0, "default": 0},
        "status": {"type": "string", "enum": ["ok", "error"], "default": "ok"},
        "error_type": {"type": "string"},
        "attributes": {"type": "object", "default": {}},
        "trace_id": {"type": "string"},
        "span_id": {"type": "string"},
        "parent_span_id": {"type": "string"},
    },
}


def schema_to_markdown() -> str:
    lines = [
        "# Agent TraceBench Trace Schema",
        "",
        "Each JSONL row represents one agent execution step.",
        "",
        "| Field | Required | Type | Description |",
        "| --- | --- | --- | --- |",
    ]
    for field in TRACE_FIELDS:
        required = "yes" if field["required"] else "no"
        lines.append(
            f"| `{field['name']}` | {required} | `{field['type']}` | {field['description']} |"
        )
    return "\n".join(lines) + "\n"
