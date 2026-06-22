from __future__ import annotations

from dataclasses import dataclass

from .bench import TraceSummary, summarize_trace
from .models import AgentStep


@dataclass(frozen=True)
class RegressionResult:
    passed: bool
    messages: list[str]
    baseline: TraceSummary
    candidate: TraceSummary


def compare_traces(
    baseline: list[AgentStep],
    candidate: list[AgentStep],
    *,
    max_latency_regression_pct: float = 10.0,
    max_token_regression_pct: float = 10.0,
    allow_new_failures: bool = False,
) -> RegressionResult:
    baseline_summary = summarize_trace(baseline)
    candidate_summary = summarize_trace(candidate)
    messages: list[str] = []

    _check_regression(
        "total latency",
        baseline_summary.total_latency_ms,
        candidate_summary.total_latency_ms,
        max_latency_regression_pct,
        messages,
    )
    _check_regression(
        "total tokens",
        baseline_summary.total_tokens,
        candidate_summary.total_tokens,
        max_token_regression_pct,
        messages,
    )
    if not allow_new_failures and candidate_summary.failed_steps > baseline_summary.failed_steps:
        messages.append(
            "failed steps increased from "
            f"{baseline_summary.failed_steps} to {candidate_summary.failed_steps}"
        )

    return RegressionResult(
        passed=not messages,
        messages=messages,
        baseline=baseline_summary,
        candidate=candidate_summary,
    )


def _check_regression(
    label: str,
    baseline_value: int,
    candidate_value: int,
    max_regression_pct: float,
    messages: list[str],
) -> None:
    if baseline_value == 0:
        if candidate_value > 0:
            messages.append(f"{label} increased from 0 to {candidate_value}")
        return

    regression_pct = ((candidate_value - baseline_value) / baseline_value) * 100
    if regression_pct > max_regression_pct:
        messages.append(
            f"{label} regressed by {regression_pct:.1f}% "
            f"({baseline_value} -> {candidate_value}; limit {max_regression_pct:.1f}%)"
        )
