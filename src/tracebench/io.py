from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .models import AgentStep


@dataclass(frozen=True)
class ValidationIssue:
    line_number: int
    message: str

    def to_dict(self) -> dict[str, object]:
        return {
            "line_number": self.line_number,
            "message": self.message,
        }


@dataclass(frozen=True)
class ValidationReport:
    path: str
    step_count: int
    issues: list[ValidationIssue]

    @property
    def passed(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "passed": self.passed,
            "step_count": self.step_count,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def read_jsonl(path: Path) -> list[AgentStep]:
    steps: list[AgentStep] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            payload = _load_line(line, line_number)
            try:
                steps.append(AgentStep.from_mapping(payload))
            except ValueError as exc:
                raise ValueError(f"Invalid trace step on line {line_number}: {exc}") from exc
    return steps


def write_jsonl(steps: list[AgentStep], path: Path) -> None:
    path.write_text(
        "".join(json.dumps(step.to_dict(), sort_keys=True) + "\n" for step in steps),
        encoding="utf-8",
    )


def validate_jsonl(path: Path) -> ValidationReport:
    issues: list[ValidationIssue] = []
    step_count = 0

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                AgentStep.from_mapping(_load_line(line, line_number))
            except ValueError as exc:
                issues.append(ValidationIssue(line_number=line_number, message=str(exc)))
            else:
                step_count += 1

    return ValidationReport(path=str(path), step_count=step_count, issues=issues)


def _load_line(line: str, line_number: int) -> dict[str, object]:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"line {line_number} must be a JSON object")
    return payload
