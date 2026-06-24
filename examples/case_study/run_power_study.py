"""Statistical power / false-positive study for the two regression checks.

Compares the aggregate threshold gate against the distribution-aware permutation
test under run-to-run noise (log-normal step latencies). For each of several
master seeds it estimates the false-positive rate (no real change) and the
detection power (a true upward shift), then reports the mean and a 95% confidence
interval across seeds. Reproduces Table V of the paper.

Usage:
    PYTHONPATH=src python examples/case_study/run_power_study.py [n30|n100|both]
"""

from __future__ import annotations

import math
import random
import sys

from tracebench.assertions import compare_step_distributions
from tracebench.models import AgentStep


def trace(rng: random.Random, n: int, sigma: float, scale: float = 1.0) -> list[AgentStep]:
    steps = []
    clock = 0
    for _ in range(n):
        dur = max(1, round(scale * 50 * math.exp(rng.gauss(0, sigma))))
        steps.append(AgentStep("retrieve", clock, clock + dur))
        clock += dur + 1
    return steps


def threshold_flags(base, cand) -> bool:
    return sum(s.latency_ms for s in cand) > 1.10 * sum(s.latency_ms for s in base)


def dist_flags(rng, base, cand, resamples) -> bool:
    return compare_step_distributions(
        base, cand, n_resamples=resamples, alpha=0.05, seed=rng.randint(0, 10**6)
    ).significant


def rate(rng, n, sigma, scale, trials, resamples) -> tuple[float, float]:
    thr = dst = 0
    for _ in range(trials):
        b = trace(rng, n, sigma)
        c = trace(rng, n, sigma, scale)
        thr += threshold_flags(b, c)
        dst += dist_flags(rng, b, c, resamples)
    return 100 * thr / trials, 100 * dst / trials


def ci95(values: list[float]) -> tuple[float, float]:
    m = sum(values) / len(values)
    if len(values) < 2:
        return m, 0.0
    sd = (sum((v - m) ** 2 for v in values) / (len(values) - 1)) ** 0.5
    return m, 1.96 * sd / math.sqrt(len(values))


def study(label, n, sigma, scale, seeds, trials, resamples):
    thr_rates, dst_rates = [], []
    for seed in seeds:
        rng = random.Random(seed)
        t, d = rate(rng, n, sigma, scale, trials, resamples)
        thr_rates.append(t)
        dst_rates.append(d)
    tm, tc = ci95(thr_rates)
    dm, dc = ci95(dst_rates)
    print(f"{label:<40} flat={tm:4.0f}+/-{tc:<4.1f}%   permutation={dm:4.0f}+/-{dc:.1f}%")


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    seeds = list(range(6))
    if which in ("n30", "both"):
        print(f"n=30 steps/config, {len(seeds)} seeds, mean +/- 95% CI")
        study("False positive (no change)", 30, 0.6, 1.00, seeds, 100, 800)
        study("Detection power (+15% shift)", 30, 0.6, 1.15, seeds, 100, 800)
        study("Detection power (+30% shift)", 30, 0.6, 1.30, seeds, 100, 800)
    if which in ("n100", "both"):
        print(f"\nn=100 steps/config, {len(seeds)} seeds, mean +/- 95% CI")
        study("False positive (no change)", 100, 0.6, 1.00, seeds, 80, 600)
        study("Detection power (+15% shift)", 100, 0.6, 1.15, seeds, 80, 600)


if __name__ == "__main__":
    main()
