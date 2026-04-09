import unittest

from backend.sub_orchestrator_graph import _select_user_tag_agents
from backend.data.state import UserTag


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
            "disengagement",
            "avoidance",
            "vague",
        ]:
            self.assertIn(expected, selected)

    def test_router_triggers_pattern_reasoning_after_two_hits(self):
        selected = _select_user_tag_agents(
            {
                "user_tag": UserTag(),
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


if __name__ == "__main__":
    unittest.main()
