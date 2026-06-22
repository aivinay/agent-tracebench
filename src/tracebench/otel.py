from __future__ import annotations

import hashlib
from collections.abc import Iterable

from .models import AgentStep


def to_otel_spans(steps: Iterable[AgentStep]) -> list[dict[str, object]]:
    materialized = list(steps)
    trace_id = _trace_id(materialized)
    spans: list[dict[str, object]] = []
    for index, step in enumerate(materialized):
        span_id = step.span_id or _hex_id(f"{trace_id}:{index}:{step.name}", 16)
        spans.append(
            {
                "trace_id": step.trace_id or trace_id,
                "span_id": span_id,
                "parent_span_id": step.parent_span_id,
                "name": step.name,
                "start_time_unix_nano": step.started_at_ms * 1_000_000,
                "end_time_unix_nano": step.ended_at_ms * 1_000_000,
                "status": {"code": "OK" if step.status == "ok" else "ERROR"},
                "attributes": _attributes(step),
            }
        )
    return spans


def _attributes(step: AgentStep) -> dict[str, object]:
    attributes = dict(step.attributes)
    attributes.update(
        {
            "tracebench.step.latency_ms": step.latency_ms,
            "tracebench.step.status": step.status,
            "gen_ai.usage.input_tokens": step.prompt_tokens,
            "gen_ai.usage.output_tokens": step.completion_tokens,
            "gen_ai.usage.total_tokens": step.total_tokens,
        }
    )
    if step.error_type:
        attributes["tracebench.error.type"] = step.error_type
    return attributes


def _trace_id(steps: list[AgentStep]) -> str:
    explicit = next((step.trace_id for step in steps if step.trace_id), None)
    if explicit:
        return explicit
    basis = "|".join(f"{step.name}:{step.started_at_ms}:{step.ended_at_ms}" for step in steps)
    return _hex_id(basis or "empty-trace", 32)


def _hex_id(value: str, length: int) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]
