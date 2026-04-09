import unittest
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage

from backend.output_graph import _sanitize_student_reply, context_compiler, output_compiler


class OutputGraphContractTest(unittest.TestCase):
    def test_sanitize_student_reply_strips_unsupported_characters(self):
        cleaned = _sanitize_student_reply("hello🙂漢字\nkeep this")

        self.assertEqual(cleaned, "hello\nkeep this")

    @patch("backend.output_graph.build_compiler_prompt", return_value="compiled prompt")
    def test_context_compiler_delegates_prompt_building(self, build_prompt):
        state = {"messages": []}

        updates = context_compiler(state)

        self.assertEqual(updates, {"compiler_prompt": "compiled prompt"})
        build_prompt.assert_called_once_with(state)

    @patch("backend.output_graph.output_llm", new=SimpleNamespace(
        invoke=lambda *_args, **_kwargs: SimpleNamespace(content="assistant reply")
    ))
    def test_output_compiler_tags_new_ai_message_not_previous_human_message(self):
        state = {
            "compiler_prompt": "prompt",
            "messages": [HumanMessage(content="student message")],
            "routing_memory": [],
            "stage": {
                "stage_related": ["purpose"],
                "contradict_target": [],
            },
        }

        updates = output_compiler(state)

        self.assertEqual(updates["messages"][0].content, "assistant reply")
        self.assertIsInstance(updates["messages"][0], AIMessage)
        self.assertEqual(updates["routing_memory"][0].content, "assistant reply")
        self.assertIsInstance(updates["routing_memory"][0], AIMessage)
        self.assertEqual(updates["purpose_message"][0].content, "assistant reply")
        self.assertIsInstance(updates["purpose_message"][0], AIMessage)

    @patch("backend.output_graph.output_llm", new=SimpleNamespace(
        invoke=lambda *_args, **_kwargs: SimpleNamespace(content="assistant reply")
    ))
    def test_output_compiler_tags_only_stage_related_queues(self):
        state = {
            "compiler_prompt": "prompt",
            "messages": [HumanMessage(content="student message")],
            "routing_memory": [],
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
