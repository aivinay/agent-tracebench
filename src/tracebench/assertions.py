from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import median

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


@dataclass(frozen=True)
class DistributionShift:
    metric: str
    step_name: str | None
    baseline_n: int
    candidate_n: int
    baseline_median: float
    candidate_median: float
    observed_shift: float
    relative_shift_pct: float
    p_value: float
    significant: bool
    n_resamples: int

    def to_dict(self) -> dict[str, object]:
        return {
            "metric": self.metric,
            "step_name": self.step_name,
            "baseline_n": self.baseline_n,
            "candidate_n": self.candidate_n,
            "baseline_median": self.baseline_median,
            "candidate_median": self.candidate_median,
            "observed_shift": self.observed_shift,
            "relative_shift_pct": self.relative_shift_pct,
            "p_value": self.p_value,
            "significant": self.significant,
            "n_resamples": self.n_resamples,
        }


def compare_step_distributions(
    baseline: list[AgentStep],
    candidate: list[AgentStep],
    *,
    metric: str = "latency_ms",
    step_name: str | None = None,
    n_resamples: int = 10000,
    alpha: float = 0.05,
    seed: int = 0,
) -> DistributionShift:
    """Permutation test for an upward shift in a per-step metric distribution.

    Tests the one-sided hypothesis that the candidate per-step ``metric`` is
    stochastically larger than the baseline, using the difference of medians as
    the test statistic. Unlike a single aggregate threshold, this accounts for
    per-step variance and run-to-run noise. The test is distribution-free and
    uses only the standard library, preserving the package's zero-dependency
    profile. Results are deterministic for a fixed ``seed``.
    """
    base_values = _metric_values(baseline, metric, step_name)
    cand_values = _metric_values(candidate, metric, step_name)
    if not base_values or not cand_values:
        raise ValueError("both traces must contain at least one matching step")

    base_med = median(base_values)
    cand_med = median(cand_values)
    observed = cand_med - base_med

    pooled = base_values + cand_values
    n_candidate = len(cand_values)
    # Deterministic resampling seed; this is not cryptographic randomness.
    rng = random.Random(seed)  # nosec B311
    at_least = 0
    for _ in range(n_resamples):
        rng.shuffle(pooled)
        perm_candidate = pooled[:n_candidate]
        perm_baseline = pooled[n_candidate:]
        if (median(perm_candidate) - median(perm_baseline)) >= observed:
            at_least += 1

    p_value = (at_least + 1) / (n_resamples + 1)
    relative = (observed / base_med * 100.0) if base_med else float("inf")
    return DistributionShift(
        metric=metric,
        step_name=step_name,
        baseline_n=len(base_values),
        candidate_n=len(cand_values),
        baseline_median=float(base_med),
        candidate_median=float(cand_med),
        observed_shift=float(observed),
        relative_shift_pct=float(relative),
        p_value=p_value,
        significant=p_value < alpha and observed > 0,
        n_resamples=n_resamples,
    )


def _metric_values(
    steps: list[AgentStep], metric: str, step_name: str | None
) -> list[float]:
    selected = [s for s in steps if step_name is None or s.name == step_name]
    if metric == "latency_ms":
        return [float(s.latency_ms) for s in selected]
    if metric == "total_tokens":
        return [float(s.total_tokens) for s in selected]
    if metric == "prompt_tokens":
        return [float(s.prompt_tokens) for s in selected]
    if metric == "completion_tokens":
        return [float(s.completion_tokens) for s in selected]
    raise ValueError(f"unsupported metric: {metric}")
