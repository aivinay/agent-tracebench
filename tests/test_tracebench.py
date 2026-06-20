import unittest

from tracebench import AgentStep, cluster_failures, replay_events, summarize_trace


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

    def test_rejects_negative_duration(self) -> None:
        with self.assertRaises(ValueError):
            AgentStep("bad", 100, 50)


if __name__ == "__main__":
    unittest.main()
