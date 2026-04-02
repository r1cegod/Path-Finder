import unittest

from backend.data.prompts.output import _compute_stage_status
from backend.data.state import (
    DEFAULT_STATE,
    FieldEntry,
    GoalsLongProfile,
    GoalsProfile,
    GoalsShortProfile,
    UniProfile,
)


class OutputPromptContractTest(unittest.TestCase):
    def test_goals_stage_status_flattens_nested_horizons(self):
        state = {
            "goals": GoalsProfile(
                done=True,
                long=GoalsLongProfile(
                    done=True,
                    income_target=FieldEntry(content="$5k/mo by 28", confidence=0.9),
                    autonomy_level=FieldEntry(content="full", confidence=0.8),
                    ownership_model=FieldEntry(content="founder", confidence=0.9),
                    team_size=FieldEntry(content="small", confidence=0.7),
                ),
                short=GoalsShortProfile(
                    done=True,
                    skill_targets=FieldEntry(content="ship products", confidence=0.8),
                    portfolio_goal=FieldEntry(content="2 real apps", confidence=0.85),
                    credential_needed=FieldEntry(content="degree", confidence=0.75),
                ),
            )
        }

        status, needed = _compute_stage_status(state, "goals")

        self.assertEqual(status, "all fields complete")
        self.assertEqual(needed, "all fields complete")

    def test_goals_stage_status_reports_nested_missing_fields(self):
        state = {
            "goals": {
                "done": False,
                "long": {
                    "done": False,
                    "income_target": {"content": "$5k/mo by 28", "confidence": 0.9},
                    "autonomy_level": {"content": "", "confidence": 0.0},
                    "ownership_model": {"content": "", "confidence": 0.0},
                    "team_size": {"content": "", "confidence": 0.0},
                },
                "short": {
                    "done": False,
                    "skill_targets": {"content": "", "confidence": 0.0},
                    "portfolio_goal": {"content": "", "confidence": 0.0},
                    "credential_needed": {"content": "", "confidence": 0.0},
                },
            }
        }

        status, needed = _compute_stage_status(state, "goals")

        self.assertEqual(status, "1/7 fields extracted")
        self.assertIn("long.autonomy_level", needed)
        self.assertIn("short.skill_targets", needed)

    def test_university_stage_status_counts_boolean_leaf(self):
        state = {
            "university": UniProfile(
                done=True,
                prestige_requirement=FieldEntry(content="mid-tier", confidence=0.9),
                target_school=FieldEntry(content="FPT", confidence=0.8),
                campus_format=FieldEntry(content="domestic", confidence=0.85),
                is_domestic=False,
            )
        }

        status, needed = _compute_stage_status(state, "university")

        self.assertEqual(status, "all fields complete")
        self.assertEqual(needed, "all fields complete")

    def test_default_state_drops_dead_fields(self):
        dead_fields = {
            "terminate",
            "thinking_limit",
            "purpose_limit",
            "goal_limit",
            "job_limit",
            "major_limit",
            "uni_limit",
            "input_token",
        }

        for field in dead_fields:
            self.assertNotIn(field, DEFAULT_STATE)


if __name__ == "__main__":
    unittest.main()
