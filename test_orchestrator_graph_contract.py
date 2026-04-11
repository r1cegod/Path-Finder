import unittest
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.messages import HumanMessage, RemoveMessage

from backend.orchestrator_graph import (
    _classify_escalation_reason,
    _normalize_escalation_reasons,
    counter_manager,
    input_parser,
    route_stage,
    stage_manager,
)


class OrchestratorGraphContractTest(unittest.TestCase):
    @patch(
        "backend.orchestrator_graph.input_llm",
        new=SimpleNamespace(
            invoke=lambda *_args, **_kwargs: SimpleNamespace(
                bypass_stage=False,
                stage_related=["thinking"],
                requested_anchor_stage="",
                message_tag=SimpleNamespace(model_dump=lambda: {"message_type": "true", "response_tone": "socratic"}),
                parental_pressure=False,
                burnout_risk=False,
                urgency=False,
                core_tension=False,
                reality_gap=False,
            )
        ),
    )
    def test_input_parser_appends_latest_human_turn_to_routing_memory(self):
        state = {
            "messages": [HumanMessage(content="student message")],
            "routing_memory": [],
            "stage": {
                "stage_related": [],
                "current_stage": "thinking",
                "anchor_stage": "thinking",
                "anchor_mode": "normal",
                "requested_anchor_stage": "",
                "contradict": False,
                "contradict_target": [],
            },
            "user_tag": None,
            "message_tag": None,
        }

        updates = input_parser(state)

        self.assertEqual(len(updates["routing_memory"]), 1)
        self.assertEqual(updates["routing_memory"][0].content, "student message")
        self.assertEqual(updates["thinking_style_message"][0].content, "student message")

    def test_input_parser_prunes_messages_before_orchestrator_prompt(self):
        class CapturingInputLLM:
            def __init__(self):
                self.prompt = None

            def invoke(self, prompt):
                self.prompt = prompt
                return SimpleNamespace(
                    bypass_stage=False,
                    stage_related=[],
                    requested_anchor_stage="",
                    message_tag=SimpleNamespace(model_dump=lambda: {"message_type": "true", "response_tone": "socratic"}),
                    parental_pressure=False,
                    burnout_risk=False,
                    urgency=False,
                    core_tension=False,
                    reality_gap=False,
                )

        fake_llm = CapturingInputLLM()
        state = {
            "messages": [
                HumanMessage(content="old one " * 900, id="m1"),
                HumanMessage(content="old two " * 900, id="m2"),
                HumanMessage(content="old three " * 900, id="m3"),
                HumanMessage(content="latest user " * 40, id="m4"),
            ],
            "routing_memory": [],
            "stage": {
                "stage_related": [],
                "current_stage": "thinking",
                "anchor_stage": "thinking",
                "anchor_mode": "normal",
                "requested_anchor_stage": "",
                "contradict": False,
                "contradict_target": [],
            },
            "user_tag": None,
            "message_tag": None,
        }

        with patch("backend.orchestrator_graph.input_llm", new=fake_llm):
            updates = input_parser(state)

        prompt_messages = fake_llm.prompt[1:]
        self.assertEqual([message.id for message in prompt_messages], ["m4"])
        self.assertEqual(len(updates["messages"]), 3)
        self.assertTrue(all(isinstance(message, RemoveMessage) for message in updates["messages"]))
        self.assertEqual(updates["routing_memory"][0].id, "m4")

    def test_classify_escalation_reason_covers_live_reason_prefixes(self):
        cases = {
            "troll_termination: 3 troll warnings": ("boundary_violation", "troll"),
            "troll: 5/10 triggers in window": ("boundary_violation", "troll"),
            "avoidance_limit: 4 consecutive avoidance turns": ("active_resistance", "avoidance"),
            "avoidance: 5/10 triggers in window": ("active_resistance", "avoidance"),
            "contradict_count: 3 consecutive stage contradictions": ("instability_in_answers", "contradict"),
            "contradict: 5/10 triggers in window": ("instability_in_answers", "contradict"),
            "disengagement_limit: 4 consecutive disengaged turns": ("cannot_engage", "disengagement"),
            "disengagement: 5/10 triggers in window": ("cannot_engage", "disengagement"),
            "vague_limit: 4 consecutive vague turns": ("cannot_engage", "vague"),
            "vague: 5/10 triggers in window": ("cannot_engage", "vague"),
            "compliance: chronic pattern, student cannot engage genuinely": ("cannot_engage", "compliance"),
            "mystery_reason: fallback": ("unknown", "mystery_reason"),
        }

        for raw_reason, expected in cases.items():
            with self.subTest(raw_reason=raw_reason):
                self.assertEqual(_classify_escalation_reason(raw_reason), expected)

    def test_normalize_escalation_reasons_chooses_highest_priority_family(self):
        normalized = _normalize_escalation_reasons(
            [
                "vague_limit: 4 consecutive vague turns",
                "avoidance_limit: 4 consecutive avoidance turns",
                "contradict_count: 3 consecutive stage contradictions",
            ]
        )

        self.assertIn("family: active_resistance", normalized)
        self.assertIn("primary_pattern: avoidance", normalized)
        self.assertIn("supporting_patterns: instability_in_answers:contradict, cannot_engage:vague", normalized)
        self.assertIn("- vague_limit: 4 consecutive vague turns", normalized)
        self.assertIn("- avoidance_limit: 4 consecutive avoidance turns", normalized)
        self.assertIn("- contradict_count: 3 consecutive stage contradictions", normalized)

    def test_normalize_escalation_reasons_preserves_unknown_fallback(self):
        normalized = _normalize_escalation_reasons(["mystery_reason: fallback"])

        self.assertEqual(
            normalized,
            "family: unknown\n"
            "primary_pattern: mystery_reason\n"
            "details:\n"
            "- mystery_reason: fallback",
        )

    def test_stage_manager_advances_to_next_unfinished_stage(self):
        state = {
            "stage": {
                "stage_related": [],
                "current_stage": "thinking",
                "anchor_stage": "thinking",
                "anchor_mode": "normal",
                "requested_anchor_stage": "",
                "contradict": False,
                "contradict_target": [],
            },
            "thinking": {"done": True},
            "purpose": {"done": False},
            "contradict_count": 0,
            "bypass_stage": False,
        }

        updates = stage_manager(state)

        self.assertEqual(updates["stage"]["current_stage"], "purpose")
        self.assertEqual(updates["stage"]["anchor_stage"], "purpose")
        self.assertEqual(updates["stage"]["anchor_mode"], "normal")
        self.assertFalse(updates["stage"]["contradict"])

    def test_stage_manager_marks_requested_done_stage_as_revisit(self):
        state = {
            "stage": {
                "stage_related": ["thinking"],
                "current_stage": "goals",
                "anchor_stage": "goals",
                "anchor_mode": "normal",
                "requested_anchor_stage": "thinking",
                "contradict": False,
                "contradict_target": [],
            },
            "thinking": {"done": True},
            "purpose": {"done": True},
            "goals": {"done": False},
            "contradict_count": 0,
            "bypass_stage": False,
        }

        updates = stage_manager(state)

        self.assertEqual(updates["stage"]["current_stage"], "goals")
        self.assertEqual(updates["stage"]["anchor_stage"], "thinking")
        self.assertEqual(updates["stage"]["anchor_mode"], "revisit")
        self.assertFalse(updates["stage"]["contradict"])

    def test_stage_manager_sets_path_debate_ready_only_under_python_gate(self):
        ready_state = {
            "stage": {
                "stage_related": [],
                "current_stage": "university",
                "anchor_stage": "university",
                "anchor_mode": "normal",
                "requested_anchor_stage": "",
                "contradict": False,
                "contradict_target": [],
            },
            "thinking": {"done": True},
            "purpose": {"done": True},
            "goals": {"done": True},
            "job": {"done": True},
            "major": {"done": True},
            "university": {"done": True},
            "user_tag": {
                "parental_pressure": False,
                "burnout_risk": False,
            },
            "contradict_count": 0,
            "bypass_stage": True,
        }
        blocked_state = dict(ready_state)
        blocked_state["user_tag"] = {"parental_pressure": True, "burnout_risk": False}

        self.assertTrue(stage_manager(ready_state)["path_debate_ready"])
        self.assertFalse(stage_manager(blocked_state)["path_debate_ready"])

    def test_counter_manager_resets_window_and_raises_window_escalation_on_tenth_turn(self):
        state = {
            "message_tag": {
                "message_type": "true",
                "response_tone": "socratic",
            },
            "stage": {
                "contradict": False,
            },
            "troll_warnings": 0,
            "compliance_turns": 0,
            "disengagement_turns": 0,
            "avoidance_turns": 0,
            "vague_turns": 0,
            "turn_count": 9,
            "contradict_count": 0,
            "trigger_window": {
                "contradict": 0,
                "compliance": 0,
                "disengagement": 0,
                "troll": 0,
                "avoidance": 5,
                "vague": 0,
            },
        }

        updates = counter_manager(state)

        self.assertTrue(updates["escalation_pending"])
        self.assertIn("family: active_resistance", updates["escalation_reason"])
        self.assertIn("avoidance: 5/10 triggers in window", updates["escalation_reason"])
        self.assertEqual(updates["turn_count"], 10)
        self.assertEqual(
            updates["trigger_window"],
            {
                "contradict": 0,
                "compliance": 0,
                "disengagement": 0,
                "troll": 0,
                "avoidance": 0,
                "vague": 0,
            },
        )

    def test_route_helpers_follow_limit_and_anchor_rules(self):
        self.assertEqual(route_stage({"bypass_stage": True}), "context_compiler")
        self.assertEqual(
            route_stage(
                {
                    "bypass_stage": False,
                    "escalation_pending": False,
                    "stage": {
                        "anchor_stage": "major",
                        "current_stage": "purpose",
                    },
                }
            ),
            "major",
        )
        self.assertEqual(
            route_stage(
                {
                    "bypass_stage": False,
                    "escalation_pending": True,
                    "stage": {
                        "anchor_stage": "major",
                        "current_stage": "purpose",
                    },
                }
            ),
            "context_compiler",
        )


if __name__ == "__main__":
    unittest.main()
