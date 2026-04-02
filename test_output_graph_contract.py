import unittest
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage

from backend.output_graph import output_compiler


class OutputGraphContractTest(unittest.TestCase):
    @patch("backend.output_graph.output_llm", new=SimpleNamespace(
        invoke=lambda *_args, **_kwargs: SimpleNamespace(content="assistant reply")
    ))
    def test_output_compiler_tags_new_ai_message_not_previous_human_message(self):
        state = {
            "compiler_prompt": "prompt",
            "messages": [HumanMessage(content="student message")],
            "stage": {
                "stage_related": ["purpose"],
                "contradict_target": [],
            },
        }

        updates = output_compiler(state)

        self.assertEqual(updates["messages"][0].content, "assistant reply")
        self.assertIsInstance(updates["messages"][0], AIMessage)
        self.assertEqual(updates["purpose_message"][0].content, "assistant reply")
        self.assertIsInstance(updates["purpose_message"][0], AIMessage)

    @patch("backend.output_graph.output_llm", new=SimpleNamespace(
        invoke=lambda *_args, **_kwargs: SimpleNamespace(content="assistant reply")
    ))
    def test_output_compiler_tags_only_stage_related_queues(self):
        state = {
            "compiler_prompt": "prompt",
            "messages": [HumanMessage(content="student message")],
            "stage": {
                "stage_related": ["job"],
                "contradict_target": ["purpose"],
            },
        }

        updates = output_compiler(state)

        self.assertEqual(updates["job_message"][0].content, "assistant reply")
        self.assertNotIn("purpose_message", updates)


if __name__ == "__main__":
    unittest.main()
