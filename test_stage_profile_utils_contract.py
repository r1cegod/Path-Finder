import unittest

from backend.data.contracts.confidence import REOPEN_CONFIDENCE_CEILING
from backend.data.state import FieldEntry, GoalsLongProfile, GoalsProfile, GoalsShortProfile, ThinkingProfile
from backend.stage_profile_utils import (
    apply_reopen_invalidation,
    count_done_fields,
    get_reentry_mode,
    normalize_stage_profile,
)


def _field(confidence: float, content: str = "set") -> FieldEntry:
    return FieldEntry(content=content, confidence=confidence)


def _thinking_profile(confidence: float = 0.91) -> ThinkingProfile:
    return ThinkingProfile(
        done=True,
        learning_mode=_field(confidence, "theoretical"),
        env_constraint=_field(confidence, "campus"),
        social_battery=_field(confidence, "solo"),
        personality_type=_field(confidence, "builder"),
        brain_type=[],
        riasec_top=[],
        riasec_scores=[],
    )


class StageProfileUtilsContractTest(unittest.TestCase):
    def test_get_reentry_mode_requires_anchor_detour(self):
        revisit_state = {
            "stage": {
                "current_stage": "purpose",
                "anchor_stage": "thinking",
                "anchor_mode": "revisit",
            }
        }
        normal_state = {
            "stage": {
                "current_stage": "thinking",
                "anchor_stage": "thinking",
                "anchor_mode": "normal",
            }
        }

        self.assertEqual(get_reentry_mode(revisit_state, "thinking"), "revisit")
        self.assertEqual(get_reentry_mode(revisit_state, "purpose"), "normal")
        self.assertEqual(get_reentry_mode(normal_state, "thinking"), "normal")

    def test_apply_reopen_invalidation_clamps_only_probe_target_when_present(self):
        state = {
            "stage_transitioned": True,
            "stage": {
                "current_stage": "purpose",
                "anchor_stage": "thinking",
                "anchor_mode": "revisit",
            },
            "stage_reasoning": {
                "thinking": "summary\nPROBE: social_battery - defend the trade-off"
            },
        }
        profile = _thinking_profile()

        updated = apply_reopen_invalidation(state, "thinking", profile)

        self.assertEqual(updated.social_battery.confidence, REOPEN_CONFIDENCE_CEILING)
        self.assertEqual(updated.learning_mode.confidence, 0.91)
        self.assertEqual(updated.env_constraint.confidence, 0.91)
        self.assertEqual(updated.personality_type.confidence, 0.91)

    def test_apply_reopen_invalidation_clamps_all_done_fields_without_probe(self):
        state = {
            "stage_transitioned": True,
            "stage": {
                "current_stage": "purpose",
                "anchor_stage": "thinking",
                "anchor_mode": "forced",
            },
            "stage_reasoning": {
                "thinking": "summary without explicit probe"
            },
        }
        profile = _thinking_profile()

        updated = apply_reopen_invalidation(state, "thinking", profile)

        self.assertEqual(updated.learning_mode.confidence, REOPEN_CONFIDENCE_CEILING)
        self.assertEqual(updated.env_constraint.confidence, REOPEN_CONFIDENCE_CEILING)
        self.assertEqual(updated.social_battery.confidence, REOPEN_CONFIDENCE_CEILING)
        self.assertEqual(updated.personality_type.confidence, REOPEN_CONFIDENCE_CEILING)

    def test_count_done_fields_tracks_goals_nested_paths(self):
        profile = GoalsProfile(
            done=False,
            long=GoalsLongProfile(
                done=False,
                income_target=_field(0.92, "$5k/mo by 28"),
                autonomy_level=_field(0.91, "full"),
                ownership_model=_field(0.93, "founder"),
                team_size=_field(0.79, "small"),
            ),
            short=GoalsShortProfile(
                done=False,
                skill_targets=_field(0.9, "ship products"),
                portfolio_goal=_field(0.79, "2 real apps"),
                credential_needed=_field(0.82, "degree"),
            ),
        )

        done_count, done_total = count_done_fields("goals", profile)

        self.assertEqual(done_count, 3)
        self.assertEqual(done_total, 4)

    def test_normalize_stage_profile_recomputes_goals_wrapper_and_nested_done_flags(self):
        profile = GoalsProfile(
            done=True,
            long=GoalsLongProfile(
                done=True,
                income_target=_field(0.92, "$5k/mo by 28"),
                autonomy_level=_field(0.91, "full"),
                ownership_model=_field(0.79, "founder"),
                team_size=_field(0.91, "small"),
            ),
            short=GoalsShortProfile(
                done=False,
                skill_targets=_field(0.9, "ship products"),
                portfolio_goal=_field(0.91, "2 real apps"),
                credential_needed=_field(0.82, "degree"),
            ),
        )

        normalized = normalize_stage_profile("goals", profile)

        self.assertFalse(normalized.done)
        self.assertFalse(normalized.long.done)
        self.assertTrue(normalized.short.done)

    def test_goals_nested_profiles_tolerate_missing_done_from_structured_output(self):
        profile = GoalsProfile(
            done=False,
            long=GoalsLongProfile(
                income_target=_field(0.92, "$5k/mo by 28"),
                autonomy_level=_field(0.91, "full"),
                ownership_model=_field(0.93, "founder"),
                team_size=_field(0.91, "small"),
            ),
            short=GoalsShortProfile(
                skill_targets=_field(0.9, "ship products"),
                portfolio_goal=_field(0.91, "2 real apps"),
                credential_needed=_field(0.82, "degree"),
            ),
        )

        normalized = normalize_stage_profile("goals", profile)

        self.assertTrue(normalized.done)
        self.assertTrue(normalized.long.done)
        self.assertTrue(normalized.short.done)


if __name__ == "__main__":
    unittest.main()
