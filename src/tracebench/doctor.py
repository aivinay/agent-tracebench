from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .io import validate_jsonl
from .schema import TRACE_JSON_SCHEMA


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
        }


def run_diagnostics(trace_file: Path | None = None) -> list[DoctorCheck]:
    checks = [_check_schema()]
    if trace_file is not None:
        checks.append(_check_trace(trace_file))
    return checks


def diagnostics_to_json(checks: list[DoctorCheck]) -> str:
    payload = {
        "passed": all(check.passed for check in checks),
        "checks": [check.to_dict() for check in checks],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def diagnostics_to_markdown(checks: list[DoctorCheck]) -> str:
    lines = [
        "# Agent TraceBench Doctor",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        status = "pass" if check.passed else "fail"
        lines.append(f"| {check.name} | {status} | {check.detail} |")
    return "\n".join(lines) + "\n"


def _check_schema() -> DoctorCheck:
    required = TRACE_JSON_SCHEMA.get("required")
    if required != ["name", "started_at_ms", "ended_at_ms"]:
        return DoctorCheck("schema", False, "required field set is unexpected")
    return DoctorCheck("schema", True, "trace schema is available")


def _check_trace(trace_file: Path) -> DoctorCheck:
    try:
        report = validate_jsonl(trace_file)
    except Exception as exc:
        return DoctorCheck("trace", False, str(exc))
    if not report.passed:
        return DoctorCheck("trace", False, f"{len(report.issues)} validation issues")
    return DoctorCheck("trace", True, f"{report.step_count} valid steps")
