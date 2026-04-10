import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage

from backend.data.state import UserTag, UserTagSummaries
from backend.sub_orchestrator_graph import (
    _build_sub_orchestrator_input,
    _limit_check_node,
    _sanitize_generated_text,
    _select_user_tag_agents,
    _should_refresh_summary,
    run_sub_orchestrator_focus,
)


class SubOrchestratorGraphContractTest(unittest.TestCase):
    def test_router_triggers_bool_workers_when_flags_are_true(self):
        selected = _select_user_tag_agents(
            {
                "user_tag": UserTag(parental_pressure=True, burnout_risk=True),
                "turn_count": 1,
                "compliance_turns": 0,
                "disengagement_turns": 0,
                "avoidance_turns": 0,
                "vague_turns": 0,
            }
        )

        self.assertIn("parental_pressure", selected)
        self.assertIn("burnout_risk", selected)
        self.assertNotIn("self_authorship", selected)

    def test_router_runs_periodic_refresh_every_five_turns(self):
        selected = _select_user_tag_agents(
            {
                "user_tag": UserTag(),
                "message_tag": {"message_type": "true", "response_tone": "socratic"},
                "turn_count": 5,
                "compliance_turns": 0,
                "disengagement_turns": 0,
                "avoidance_turns": 0,
                "vague_turns": 0,
            }
        )

        for expected in [
            "parental_pressure",
            "burnout_risk",
            "urgency",
            "core_tension",
            "reality_gap",
            "self_authorship",
            "compliance",
        ]:
            self.assertIn(expected, selected)
        for not_expected in ["disengagement", "avoidance", "vague"]:
            self.assertNotIn(not_expected, selected)

    def test_router_triggers_pattern_reasoning_after_two_hits(self):
        selected = _select_user_tag_agents(
            {
                "user_tag": UserTag(),
                "message_tag": {"message_type": "true", "response_tone": "socratic"},
                "turn_count": 3,
                "compliance_turns": 0,
                "disengagement_turns": 2,
                "avoidance_turns": 2,
                "vague_turns": 2,
            }
        )

        self.assertIn("disengagement", selected)
        self.assertIn("avoidance", selected)
        self.assertIn("vague", selected)
        self.assertNotIn("compliance", selected)

    def test_limit_check_prunes_routing_memory_and_stashes_retired_slice(self):
        state = {
            "routing_memory": [
                HumanMessage(content="x " * 2000, id="h1"),
                AIMessage(content="y " * 2000, id="a2"),
                HumanMessage(content="z " * 2000, id="h3"),
                AIMessage(content="q " * 2000, id="a4"),
            ],
            "patches": [],
            "summary_patches": [],
        }

        updates = _limit_check_node(state)

        self.assertTrue(updates["routing_memory_over_limit"])
        self.assertEqual(len(updates["retired_routing_memory"]), 3)
        self.assertEqual(len(updates["routing_memory"]), 1)
        self.assertEqual(len(updates["routing_memory_updates"]), 3)
        self.assertTrue(all(isinstance(item, RemoveMessage) for item in updates["routing_memory_updates"]))

    def test_limit_check_skips_summary_path_when_under_budget(self):
        state = {
            "routing_memory": [HumanMessage(content="short", id="h1")],
            "user_tag_summaries": UserTagSummaries(),
            "patches": [],
            "summary_patches": [],
        }

        updates = _limit_check_node(state)

        self.assertFalse(updates["routing_memory_over_limit"])
        self.assertEqual(updates["retired_routing_memory"], [])
        self.assertEqual(len(updates["routing_memory"]), 1)
        self.assertEqual(updates["routing_memory_updates"], [])

    def test_summary_refresh_skips_empty_side_fields(self):
        state = {
            "user_tag": UserTag(),
            "user_tag_summaries": UserTagSummaries(),
            "message_tag": {"message_type": "true", "response_tone": "socratic"},
            "compliance_turns": 0,
            "disengagement_turns": 0,
            "avoidance_turns": 0,
            "vague_turns": 0,
        }

        self.assertFalse(_should_refresh_summary(state, "compliance"))
        self.assertFalse(_should_refresh_summary(state, "reality_gap"))
        self.assertTrue(_should_refresh_summary(state, "self_authorship"))

    def test_summary_refresh_keeps_existing_pattern_fields_live(self):
        state = {
            "user_tag": UserTag(),
            "user_tag_summaries": UserTagSummaries(compliance="Old compliance signal"),
            "message_tag": {"message_type": "true", "response_tone": "socratic"},
            "compliance_turns": 0,
            "disengagement_turns": 0,
            "avoidance_turns": 0,
            "vague_turns": 0,
        }

        self.assertTrue(_should_refresh_summary(state, "compliance"))

    def test_sanitize_generated_text_removes_mixed_script_noise(self):
        cleaned = _sanitize_generated_text("The student is postponing present能力 concerns.")

        self.assertEqual(cleaned, "The student is postponing present concerns.")

    def test_build_sub_orchestrator_input_sets_eval_defaults(self):
        sub_state = _build_sub_orchestrator_input(
            {
                "messages": [HumanMessage(content="hello")],
                "routing_memory": [AIMessage(content="reply")],
                "turn_count": 5,
            }
        )

        self.assertEqual(len(sub_state["messages"]), 1)
        self.assertEqual(len(sub_state["routing_memory"]), 1)
        self.assertEqual(sub_state["turn_count"], 5)
        self.assertEqual(sub_state["selected_agents"], [])
        self.assertEqual(sub_state["patches"], [])
        self.assertEqual(sub_state["summary_patches"], [])

    @patch("backend.sub_orchestrator_graph._sub_orchestrator_summarizer_focus_graph.invoke")
    def test_run_sub_orchestrator_focus_routes_to_summarizer_graph(self, mock_invoke):
        mock_invoke.return_value = {"routing_memory_over_limit": True}

        result = run_sub_orchestrator_focus({"routing_memory": [HumanMessage(content="x")]}, target="summarizer")

        self.assertTrue(result["routing_memory_over_limit"])
        self.assertEqual(mock_invoke.call_count, 1)

    @patch("backend.sub_orchestrator_graph._sub_orchestrator_worker_focus_graph.invoke")
    def test_run_sub_orchestrator_focus_routes_to_worker_graph(self, mock_invoke):
        mock_invoke.return_value = {"user_tag": {"burnout_risk": True}}

        result = run_sub_orchestrator_focus({"routing_memory": [HumanMessage(content="x")]}, target="worker")

        self.assertTrue(result["user_tag"]["burnout_risk"])
        self.assertEqual(mock_invoke.call_count, 1)


if __name__ == "__main__":
    unittest.main()
