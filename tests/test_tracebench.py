import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tracebench import (
    TRACE_JSON_SCHEMA,
    AgentStep,
    cluster_failures,
    compare_traces,
    estimate_cost,
    latency_outliers,
    read_jsonl,
    redact_steps,
    regression_to_markdown,
    replay_events,
    schema_to_markdown,
    summarize_trace,
    to_otel_spans,
    validate_jsonl,
    write_jsonl,
)
from tracebench.cli import run


class TraceBenchTests(unittest.TestCase):
    def test_summarizes_latency_tokens_and_failures(self) -> None:
        steps = [
            AgentStep("plan", 0, 100, prompt_tokens=10, completion_tokens=5),
            AgentStep("tool.search", 105, 405, prompt_tokens=20, completion_tokens=10),
            AgentStep("final", 410, 460, status="error", error_type="tool_timeout"),
        ]

        summary = summarize_trace(steps)

        self.assertEqual(summary.step_count, 3)
        self.assertEqual(summary.total_latency_ms, 450)
        self.assertEqual(summary.p95_step_latency_ms, 300)
        self.assertEqual(summary.total_tokens, 45)
        self.assertEqual(summary.failed_steps, 1)
        self.assertEqual(cluster_failures(steps), {"tool_timeout": 1})

    def test_replay_events_are_ordered_by_start_time(self) -> None:
        steps = [
            AgentStep("second", 50, 75),
            AgentStep("first", 10, 20),
        ]

        events = replay_events(steps)

        self.assertEqual([event["name"] for event in events], ["first", "second"])
        self.assertEqual([event["offset_ms"] for event in events], [0, 40])
        self.assertEqual([event["total_tokens"] for event in events], [0, 0])

    def test_rejects_negative_duration(self) -> None:
        with self.assertRaises(ValueError):
            AgentStep("bad", 100, 50)

    def test_jsonl_roundtrip_and_otel_export(self) -> None:
        steps = [
            AgentStep(
                "model",
                0,
                100,
                prompt_tokens=100,
                completion_tokens=25,
                attributes={"model": "test-model"},
            )
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "trace.jsonl"
            write_jsonl(steps, path)
            loaded = read_jsonl(path)

        spans = to_otel_spans(loaded)

        self.assertEqual(loaded[0].total_tokens, 125)
        self.assertEqual(spans[0]["attributes"]["gen_ai.usage.total_tokens"], 125)
        self.assertEqual(spans[0]["status"], {"code": "OK"})

    def test_compare_detects_regression(self) -> None:
        baseline = [AgentStep("model", 0, 100, prompt_tokens=10)]
        candidate = [AgentStep("model", 0, 150, prompt_tokens=20)]

        result = compare_traces(
            baseline,
            candidate,
            max_latency_regression_pct=20,
            max_token_regression_pct=20,
        )

        self.assertFalse(result.passed)
        self.assertTrue(any("latency" in message for message in result.messages))

    def test_cost_outliers_and_redaction(self) -> None:
        steps = [
            AgentStep(
                "fast",
                0,
                100,
                prompt_tokens=100,
                completion_tokens=50,
                attributes={"prompt": "secret"},
            ),
            AgentStep(
                "slow",
                0,
                500,
                prompt_tokens=200,
                completion_tokens=100,
                attributes={"safe": "value"},
            ),
        ]

        cost = estimate_cost(steps, input_cost_per_million=1.0, output_cost_per_million=2.0)
        outliers = latency_outliers(steps, threshold_ms=300)
        redacted = redact_steps(steps)

        self.assertEqual(cost["total_tokens"], 450.0)
        self.assertEqual([step.name for step in outliers], ["slow"])
        self.assertEqual(redacted[0].attributes["prompt"], "[redacted]")
        self.assertEqual(redacted[1].attributes["safe"], "value")

    def test_validation_reports_line_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.jsonl"
            path.write_text(
                "\n".join(
                    [
                        '{"name":"ok","started_at_ms":0,"ended_at_ms":1}',
                        '{"name":"bad","started_at_ms":3,"ended_at_ms":2}',
                        '{"name":"missing"}',
                        "not-json",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = validate_jsonl(path)

        self.assertFalse(report.passed)
        self.assertEqual(report.step_count, 1)
        self.assertEqual([issue.line_number for issue in report.issues], [2, 3, 4])
        self.assertIn("ended_at_ms", report.issues[0].message)

    def test_schema_outputs_are_available(self) -> None:
        schema = schema_to_markdown()

        self.assertIn("Agent TraceBench Trace Schema", schema)
        self.assertEqual(TRACE_JSON_SCHEMA["required"], ["name", "started_at_ms", "ended_at_ms"])

    def test_regression_markdown_report_lists_findings(self) -> None:
        result = compare_traces(
            [AgentStep("model", 0, 100, prompt_tokens=10)],
            [AgentStep("model", 0, 160, prompt_tokens=30)],
            max_latency_regression_pct=10,
            max_token_regression_pct=10,
        )

        report = regression_to_markdown(result)

        self.assertIn("Status: failed", report)
        self.assertIn("Total latency", report)

    def test_cli_schema_validate_and_compare(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline = Path(tmpdir) / "baseline.jsonl"
            candidate = Path(tmpdir) / "candidate.jsonl"
            write_jsonl([AgentStep("model", 0, 100, prompt_tokens=10)], baseline)
            write_jsonl([AgentStep("model", 0, 160, prompt_tokens=30)], candidate)

            schema_out = io.StringIO()
            with contextlib.redirect_stdout(schema_out):
                schema_code = run(["schema", "--format", "markdown"])

            validate_out = io.StringIO()
            with contextlib.redirect_stdout(validate_out):
                validate_code = run(["validate", str(baseline), "--format", "json"])

            compare_out = io.StringIO()
            with contextlib.redirect_stdout(compare_out):
                compare_code = run(
                    [
                        "compare",
                        str(baseline),
                        str(candidate),
                        "--format",
                        "markdown",
                    ]
                )

        self.assertEqual(schema_code, 0)
        self.assertIn("| Field |", schema_out.getvalue())
        self.assertEqual(validate_code, 0)
        self.assertTrue(json.loads(validate_out.getvalue())["passed"])
        self.assertEqual(compare_code, 2)
        self.assertIn("Status: failed", compare_out.getvalue())

    def test_cli_invalid_input_returns_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.jsonl"
            path.write_text('{"name": "bad"}\n', encoding="utf-8")

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = run(["summarize", str(path)])

        self.assertEqual(code, 1)
        self.assertIn("tracebench:", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
