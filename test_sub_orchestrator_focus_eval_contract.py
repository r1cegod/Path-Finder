import unittest

from backend.sub_orchestrator_focus_eval import build_focus_eval_state, split_focus_eval_payload


class SubOrchestratorFocusEvalContractTest(unittest.TestCase):
    def test_split_focus_eval_payload_separates_metadata(self):
        payload, metadata = split_focus_eval_payload(
            {
                "eval_case": "case-a",
                "expected_checks": ["x"],
                "notes": "memo",
                "routing_memory": [],
            }
        )

        self.assertEqual(payload, {"routing_memory": []})
        self.assertEqual(metadata["eval_case"], "case-a")
        self.assertEqual(metadata["expected_checks"], ["x"])
        self.assertEqual(metadata["notes"], "memo")

    def test_build_focus_eval_state_mirrors_messages_into_routing_memory(self):
        state, metadata = build_focus_eval_state(
            {
                "eval_case": "case-b",
                "messages": [{"role": "user", "content": "student message"}],
            },
            target="worker",
        )

        self.assertEqual(metadata["eval_case"], "case-b")
        self.assertEqual(len(state["messages"]), 1)
        self.assertEqual(len(state["routing_memory"]), 1)
        self.assertEqual(state["routing_memory"][0].content, "student message")

    def test_build_focus_eval_state_rejects_missing_focus_queue(self):
        with self.assertRaisesRegex(ValueError, "requires 'routing_memory' or fallback 'messages'"):
            build_focus_eval_state({}, target="summarizer")


if __name__ == "__main__":
    unittest.main()
