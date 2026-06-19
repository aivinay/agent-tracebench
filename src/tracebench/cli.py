from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bench import cluster_failures, summarize_trace
from .models import AgentStep


def main() -> None:
    parser = argparse.ArgumentParser(prog="tracebench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summarize = subparsers.add_parser("summarize", help="Summarize a JSONL agent trace.")
    summarize.add_argument("trace_file", type=Path)

    args = parser.parse_args()
    if args.command == "summarize":
        steps = _read_jsonl(args.trace_file)
        summary = summarize_trace(steps)
        payload = {
            "summary": summary.__dict__,
            "failures": cluster_failures(steps),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))


def _read_jsonl(path: Path) -> list[AgentStep]:
    steps: list[AgentStep] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
            steps.append(AgentStep.from_mapping(payload))
    return steps


if __name__ == "__main__":
    main()
