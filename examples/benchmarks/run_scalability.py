"""Scalability benchmark for Agent TraceBench.

Measures wall-clock time of the core operations (summarize, OpenTelemetry
export, compare, JSONL read) over trace sizes from 1e3 to 5e5 steps, reporting
the median and the min-max spread over repeated runs. Reproduces Table VI and
Figure 2 of the paper.

Usage:
    PYTHONPATH=src python examples/benchmarks/run_scalability.py
"""

from __future__ import annotations

import random
import statistics
import time
from pathlib import Path

from tracebench.assertions import compare_traces
from tracebench.bench import summarize_trace
from tracebench.io import read_jsonl, write_jsonl
from tracebench.models import AgentStep
from tracebench.otel import to_otel_spans

RNG = random.Random(7)


def make_trace(n: int) -> list[AgentStep]:
    steps = []
    clock = 0
    for _ in range(n):
        dur = RNG.randint(20, 500)
        steps.append(
            AgentStep(
                name="step",
                started_at_ms=clock,
                ended_at_ms=clock + dur,
                prompt_tokens=RNG.randint(10, 400),
                completion_tokens=RNG.randint(10, 400),
            )
        )
        clock += dur + 1
    return steps


def timed(fn, repeats: int) -> tuple[float, float, float]:
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    return statistics.median(samples), min(samples), max(samples)


def main() -> None:
    sizes = [1000, 10000, 100000, 500000]
    header = f"{'N':>8} {'summarize ms (med[min-max])':>30} {'otel ms':>22} {'compare ms':>22} {'read ms':>22}"
    print(header)
    for n in sizes:
        steps = make_trace(n)
        repeats = 5 if n <= 100000 else 3
        s_med, s_lo, s_hi = timed(lambda: summarize_trace(steps), repeats)
        o_med, o_lo, o_hi = timed(lambda: to_otel_spans(steps), repeats)
        c_med, c_lo, c_hi = timed(lambda: compare_traces(steps, steps), repeats)
        path = Path(f"/tmp/scale_{n}.jsonl")
        write_jsonl(steps, path)
        r_med, r_lo, r_hi = timed(lambda: read_jsonl(path), max(1, repeats - 2))
        print(
            f"{n:>8} "
            f"{s_med:>10.1f} [{s_lo:.1f}-{s_hi:.1f}]   "
            f"{o_med:>8.1f} [{o_lo:.0f}-{o_hi:.0f}]   "
            f"{c_med:>8.1f} [{c_lo:.0f}-{c_hi:.0f}]   "
            f"{r_med:>8.1f} [{r_lo:.0f}-{r_hi:.0f}]"
        )
        print(f"         summarize throughput: {n / (s_med / 1000.0):,.0f} steps/s")


if __name__ == "__main__":
    main()
