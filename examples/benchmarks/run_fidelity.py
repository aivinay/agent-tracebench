"""Correctness / fidelity checks for Agent TraceBench.

Generates a controlled trace with known properties and verifies OpenTelemetry
span validity, lossless JSONL round-trips, exact failure clustering, complete
redaction of sensitive attributes, and latency-outlier detection. Reproduces
Table VII of the paper. Deterministic for the fixed seed below.

Usage:
    PYTHONPATH=src python examples/benchmarks/run_fidelity.py
"""

from __future__ import annotations

import collections
import random
import tempfile
from pathlib import Path

from tracebench.analysis import latency_outliers, redact_steps
from tracebench.bench import cluster_failures
from tracebench.io import read_jsonl, write_jsonl
from tracebench.models import AgentStep
from tracebench.otel import to_otel_spans

SEED = 20260623
ERROR_TYPES = ["timeout", "tool_error", "rate_limit", "parse_error"]


def gen_trace(n: int, fail_rate: float, seed: int) -> list[AgentStep]:
    rng = random.Random(seed)
    steps = []
    clock = 0
    for _ in range(n):
        dur = int(rng.lognormvariate(4.6, 0.6)) + 5
        status, err = "ok", None
        if rng.random() < fail_rate:
            status, err = "error", rng.choice(ERROR_TYPES)
        steps.append(
            AgentStep(
                name="step",
                started_at_ms=clock,
                ended_at_ms=clock + dur,
                prompt_tokens=int(rng.lognormvariate(5.2, 0.5)),
                completion_tokens=int(rng.lognormvariate(4.4, 0.6)),
                status=status,
                error_type=err,
                attributes={"model": "m", "api_key": "sk-secret", "prompt": "hello"},
            )
        )
        clock += dur + rng.randint(1, 8)
    return steps


def main() -> None:
    trace = gen_trace(500, 0.0, SEED)

    spans = to_otel_spans(trace)
    valid = sum(
        1
        for sp in spans
        if sp["trace_id"]
        and sp["span_id"]
        and sp["end_time_unix_nano"] >= sp["start_time_unix_nano"]
        and sp["status"]["code"] in ("OK", "ERROR")
        and "gen_ai.usage.total_tokens" in sp["attributes"]
    )
    print(f"OpenTelemetry span validity: {valid}/{len(spans)} valid")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "rt.jsonl"
        write_jsonl(trace, path)
        loaded = read_jsonl(path)
    roundtrip = len(loaded) == len(trace) and all(
        a.to_dict() == b.to_dict() for a, b in zip(loaded, trace)
    )
    print(f"JSONL round-trip preserves all steps: {roundtrip}")

    failing = gen_trace(300, 0.2, SEED + 1)
    injected = collections.Counter(s.error_type for s in failing if s.status == "error")
    recovered = cluster_failures(failing)
    print(f"Failure clustering exact match: {recovered == dict(sorted(injected.items()))}")
    print(f"  injected/recovered counts: {recovered}")

    redacted = redact_steps(trace)
    leaks = sum(
        1
        for s in redacted
        if s.attributes.get("api_key") != "[redacted]" or s.attributes.get("prompt") != "[redacted]"
    )
    benign_kept = all(s.attributes.get("model") == "m" for s in redacted)
    print(f"Redaction leaks: {leaks} (benign attribute preserved: {benign_kept})")

    outliers = latency_outliers(trace, median_multiplier=2.0)
    print(f"Latency outliers (> 2x median): {len(outliers)}/{len(trace)}")


if __name__ == "__main__":
    main()
