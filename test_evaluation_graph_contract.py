import copy
import unittest

from langchain_core.messages import HumanMessage

from backend.data.state import DEFAULT_STATE
from backend.evaluation_graph import normalize_evaluation_state


class EvaluationGraphContractTest(unittest.TestCase):
    def test_stage_queue_only_seeds_messages_and_stage_related(self):
        state = copy.deepcopy(DEFAULT_STATE)
        state["thinking_style_message"] = [HumanMessage(content="test")]

        updates = normalize_evaluation_state("thinking", state)

        self.assertEqual(len(updates["messages"]), 1)
        self.assertEqual(updates["messages"][0].content, "test")
        self.assertEqual(updates["stage"]["stage_related"], ["thinking"])
        self.assertEqual(updates["stage"]["current_stage"], "thinking")

    def test_explicit_stage_related_is_preserved(self):
        state = copy.deepcopy(DEFAULT_STATE)
        state["thinking_style_message"] = [HumanMessage(content="test")]
        state["stage"] = {
            "stage_related": ["purpose"],
            "rebound": False,
            "current_stage": "thinking",
            "contradict": False,
            "contradict_target": [],
            "forced_stage": "",
        }

        updates = normalize_evaluation_state("thinking", state)

        self.assertNotIn("stage", updates)
        self.assertEqual(updates["messages"][0].content, "test")


if __name__ == "__main__":
    unittest.main()
