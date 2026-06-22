from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import ceil

from .models import AgentStep


@dataclass(frozen=True)
class TraceSummary:
    step_count: int
    total_latency_ms: int
    p95_step_latency_ms: int
    total_tokens: int
    failed_steps: int


def summarize_trace(steps: Iterable[AgentStep]) -> TraceSummary:
    materialized = list(steps)
    latencies = sorted(step.latency_ms for step in materialized)
    p95_latency = _percentile(latencies, 95)

    return TraceSummary(
        step_count=len(materialized),
        total_latency_ms=sum(latencies),
        p95_step_latency_ms=p95_latency,
        total_tokens=sum(step.total_tokens for step in materialized),
        failed_steps=sum(1 for step in materialized if step.status != "ok"),
    )


def cluster_failures(steps: Iterable[AgentStep]) -> dict[str, int]:
    clusters: dict[str, int] = {}
    for step in steps:
        if step.status == "ok":
            continue
        key = step.error_type or "unknown"
        clusters[key] = clusters.get(key, 0) + 1
    return dict(sorted(clusters.items()))


def replay_events(steps: Iterable[AgentStep]) -> list[dict[str, object]]:
    ordered = sorted(steps, key=lambda step: (step.started_at_ms, step.name))
    if not ordered:
        return []

    trace_start = ordered[0].started_at_ms
    return [
        {
            "offset_ms": step.started_at_ms - trace_start,
            "name": step.name,
            "latency_ms": step.latency_ms,
            "status": step.status,
            "total_tokens": step.total_tokens,
        }
        for step in ordered
    ]


def summary_to_markdown(summary: TraceSummary, failures: dict[str, int]) -> str:
    lines = [
        "# Agent TraceBench Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Steps | {summary.step_count} |",
        f"| Total latency (ms) | {summary.total_latency_ms} |",
        f"| p95 step latency (ms) | {summary.p95_step_latency_ms} |",
        f"| Total tokens | {summary.total_tokens} |",
        f"| Failed steps | {summary.failed_steps} |",
    ]
    if failures:
        lines.extend(["", "## Failures", ""])
        for error_type, count in failures.items():
            lines.append(f"- {error_type}: {count}")
    return "\n".join(lines) + "\n"


def _percentile(values: list[int], percentile: int) -> int:
    if not values:
        return 0
    rank = max(1, ceil((percentile / 100) * len(values)))
    return values[rank - 1]
