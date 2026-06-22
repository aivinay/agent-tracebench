from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .analysis import estimate_cost, latency_outliers, redact_steps
from .assertions import compare_traces
from .bench import cluster_failures, replay_events, summarize_trace, summary_to_markdown
from .doctor import diagnostics_to_json, diagnostics_to_markdown, run_diagnostics
from .io import read_jsonl, validate_jsonl, write_jsonl
from .otel import to_otel_spans
from .reports import regression_to_markdown, validation_to_text
from .schema import TRACE_JSON_SCHEMA, schema_to_markdown


def main() -> None:
    raise SystemExit(run())


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tracebench",
        description="Inspect, compare, redact, and export JSONL traces from LLM applications.",
    )
    parser.add_argument("--version", action="version", version=f"tracebench {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    schema = subparsers.add_parser("schema", help="Print the trace schema.")
    schema.add_argument("--format", choices=["json", "markdown"], default="json")

    validate = subparsers.add_parser("validate", help="Validate a JSONL agent trace.")
    validate.add_argument("trace_file", type=Path)
    validate.add_argument("--format", choices=["json", "text"], default="text")

    doctor = subparsers.add_parser(
        "doctor",
        help="Check local installation and optional trace input.",
    )
    doctor.add_argument("--trace-file", type=Path, help="Optional JSONL trace to validate.")
    doctor.add_argument("--format", choices=["json", "markdown"], default="markdown")

    summarize = subparsers.add_parser("summarize", help="Summarize a JSONL agent trace.")
    summarize.add_argument("trace_file", type=Path)
    summarize.add_argument("--format", choices=["json", "markdown"], default="json")

    replay = subparsers.add_parser("replay", help="Emit replay events in causal order.")
    replay.add_argument("trace_file", type=Path)

    otel = subparsers.add_parser(
        "otel",
        help="Export trace steps as OpenTelemetry-compatible span JSON.",
    )
    otel.add_argument("trace_file", type=Path)

    outliers = subparsers.add_parser("outliers", help="List steps with unusually high latency.")
    outliers.add_argument("trace_file", type=Path)
    outliers.add_argument("--threshold-ms", type=int)
    outliers.add_argument("--median-multiplier", type=float, default=2.0)

    cost = subparsers.add_parser(
        "cost",
        help="Estimate trace token cost from per-million token rates.",
    )
    cost.add_argument("trace_file", type=Path)
    cost.add_argument("--input-cost-per-million", required=True, type=float)
    cost.add_argument("--output-cost-per-million", required=True, type=float)

    redact = subparsers.add_parser(
        "redact",
        help="Write a JSONL trace with sensitive attributes redacted.",
    )
    redact.add_argument("trace_file", type=Path)
    redact.add_argument("--output", "-o", required=True, type=Path)
    redact.add_argument(
        "--key",
        action="append",
        dest="keys",
        help="Attribute key to redact; may be repeated.",
    )

    compare = subparsers.add_parser(
        "compare",
        help="Compare a candidate trace against a baseline trace.",
    )
    compare.add_argument("baseline", type=Path)
    compare.add_argument("candidate", type=Path)
    compare.add_argument("--max-latency-regression-pct", type=float, default=10.0)
    compare.add_argument("--max-token-regression-pct", type=float, default=10.0)
    compare.add_argument("--allow-new-failures", action="store_true")
    compare.add_argument("--format", choices=["json", "markdown"], default="json")

    args = parser.parse_args(argv)
    try:
        return _run_command(args)
    except (OSError, ValueError) as exc:
        print(f"tracebench: {exc}", file=sys.stderr)
        return 1


def _run_command(args: argparse.Namespace) -> int:
    if args.command == "schema":
        if args.format == "markdown":
            print(schema_to_markdown(), end="")
            return 0
        print(json.dumps(TRACE_JSON_SCHEMA, indent=2, sort_keys=True))
        return 0

    if args.command == "validate":
        report = validate_jsonl(args.trace_file)
        if args.format == "json":
            print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        else:
            print(validation_to_text(report), end="")
        return 0 if report.passed else 1

    if args.command == "doctor":
        checks = run_diagnostics(args.trace_file)
        if args.format == "json":
            print(diagnostics_to_json(checks))
        else:
            print(diagnostics_to_markdown(checks), end="")
        return 0 if all(check.passed for check in checks) else 1

    if args.command == "summarize":
        return _summarize(args)

    if args.command == "replay":
        print(json.dumps(replay_events(read_jsonl(args.trace_file)), indent=2, sort_keys=True))
        return 0

    if args.command == "otel":
        payload = {"resource_spans": to_otel_spans(read_jsonl(args.trace_file))}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "outliers":
        steps = latency_outliers(
            read_jsonl(args.trace_file),
            threshold_ms=args.threshold_ms,
            median_multiplier=args.median_multiplier,
        )
        print(json.dumps([step.to_dict() for step in steps], indent=2, sort_keys=True))
        return 0

    if args.command == "cost":
        payload = estimate_cost(
            read_jsonl(args.trace_file),
            input_cost_per_million=args.input_cost_per_million,
            output_cost_per_million=args.output_cost_per_million,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "redact":
        write_jsonl(
            redact_steps(
                read_jsonl(args.trace_file),
                redact_keys=set(args.keys) if args.keys else None,
            ),
            args.output,
        )
        return 0

    if args.command == "compare":
        result = compare_traces(
            read_jsonl(args.baseline),
            read_jsonl(args.candidate),
            max_latency_regression_pct=args.max_latency_regression_pct,
            max_token_regression_pct=args.max_token_regression_pct,
            allow_new_failures=args.allow_new_failures,
        )
        if args.format == "markdown":
            print(regression_to_markdown(result), end="")
        else:
            print(
                json.dumps(
                    {
                        "passed": result.passed,
                        "messages": result.messages,
                        "baseline": result.baseline.__dict__,
                        "candidate": result.candidate.__dict__,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        if not result.passed:
            return 2

    return 0


def _summarize(args: argparse.Namespace) -> int:
    steps = read_jsonl(args.trace_file)
    summary = summarize_trace(steps)
    failures = cluster_failures(steps)
    if args.format == "markdown":
        print(summary_to_markdown(summary, failures), end="")
        return 0
    payload = {
        "summary": summary.__dict__,
        "failures": failures,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
