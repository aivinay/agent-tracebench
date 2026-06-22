from __future__ import annotations

from .assertions import RegressionResult
from .io import ValidationReport


def regression_to_markdown(result: RegressionResult) -> str:
    status = "passed" if result.passed else "failed"
    lines = [
        "# Agent TraceBench Comparison",
        "",
        f"Status: {status}",
        "",
        "| Metric | Baseline | Candidate |",
        "| --- | ---: | ---: |",
        f"| Steps | {result.baseline.step_count} | {result.candidate.step_count} |",
        (
            "| Total latency (ms) | "
            f"{result.baseline.total_latency_ms} | {result.candidate.total_latency_ms} |"
        ),
        (
            "| p95 step latency (ms) | "
            f"{result.baseline.p95_step_latency_ms} | {result.candidate.p95_step_latency_ms} |"
        ),
        f"| Total tokens | {result.baseline.total_tokens} | {result.candidate.total_tokens} |",
        f"| Failed steps | {result.baseline.failed_steps} | {result.candidate.failed_steps} |",
    ]

    if result.messages:
        lines.extend(["", "## Findings", ""])
        lines.extend(f"- {message}" for message in result.messages)

    return "\n".join(lines) + "\n"


def validation_to_text(report: ValidationReport) -> str:
    if report.passed:
        return f"ok: {report.step_count} valid steps in {report.path}\n"

    lines = [f"failed: {len(report.issues)} issue(s) in {report.path}"]
    lines.extend(f"line {issue.line_number}: {issue.message}" for issue in report.issues)
    return "\n".join(lines) + "\n"
