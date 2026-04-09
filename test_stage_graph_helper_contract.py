import unittest

from backend.data.contracts.confidence import REOPEN_CONFIDENCE_CEILING
from backend.data.state import (
    FieldEntry,
    GoalsLongProfile,
    GoalsProfile,
    GoalsShortProfile,
    JobProfile,
    MajorProfile,
    PurposeProfile,
    ThinkingProfile,
    UniProfile,
)
from backend.goals_graph import get_current_stage as goals_get_current_stage
from backend.goals_graph import reopen_invalidator_node as goals_reopen_invalidator_node
from backend.job_graph import get_current_stage as job_get_current_stage
from backend.job_graph import reopen_invalidator_node as job_reopen_invalidator_node
from backend.job_graph import route_after_planner as job_route_after_planner
from backend.major_graph import get_current_stage as major_get_current_stage
from backend.major_graph import reopen_invalidator_node as major_reopen_invalidator_node
from backend.major_graph import route_after_planner as major_route_after_planner
from backend.purpose_graph import get_current_stage as purpose_get_current_stage
from backend.purpose_graph import reopen_invalidator_node as purpose_reopen_invalidator_node
from backend.thinking_graph import get_current_stage as thinking_get_current_stage
from backend.thinking_graph import reopen_invalidator_node as thinking_reopen_invalidator_node
from backend.uni_graph import get_current_stage as uni_get_current_stage
from backend.uni_graph import reopen_invalidator_node as uni_reopen_invalidator_node
from backend.uni_graph import route_after_planner as uni_route_after_planner


def _field(confidence: float, content: str = "set") -> FieldEntry:
    return FieldEntry(content=content, confidence=confidence)


def _get_nested(mapping: dict, path: tuple[str, ...]) -> object:
    current = mapping
    for part in path:
        current = current[part]
    return current


class StageGraphHelperContractTest(unittest.TestCase):
    def test_get_current_stage_prefers_anchor_stage_across_graphs(self):
        state = {
            "stage": {
                "current_stage": "major",
                "anchor_stage": "purpose",
            }
        }
        cases = {
            "thinking": thinking_get_current_stage,
            "purpose": purpose_get_current_stage,
            "goals": goals_get_current_stage,
            "job": job_get_current_stage,
            "major": major_get_current_stage,
            "university": uni_get_current_stage,
        }

        for stage_name, getter in cases.items():
            with self.subTest(stage_name=stage_name):
                self.assertEqual(getter(state), "purpose")

    def test_get_current_stage_falls_back_to_stage_default_when_missing(self):
        cases = {
            "thinking": (thinking_get_current_stage, "thinking"),
            "purpose": (purpose_get_current_stage, "purpose"),
            "goals": (goals_get_current_stage, "goals"),
            "job": (job_get_current_stage, "job"),
            "major": (major_get_current_stage, "major"),
            "university": (uni_get_current_stage, "university"),
        }

        for stage_name, (getter, expected) in cases.items():
            with self.subTest(stage_name=stage_name):
                self.assertEqual(getter({}), expected)

    def test_reopen_invalidator_nodes_clamp_targeted_probe_field_across_all_stage_graphs(self):
        base_stage = {
            "current_stage": "university",
            "anchor_mode": "revisit",
        }
        cases = [
            (
                "thinking",
                thinking_reopen_invalidator_node,
                "thinking",
                "university",
                ThinkingProfile(
                    done=True,
                    learning_mode=_field(0.91, "theoretical"),
                    env_constraint=_field(0.91, "campus"),
                    social_battery=_field(0.91, "solo"),
                    personality_type=_field(0.91, "builder"),
                    brain_type=[],
                    riasec_top=[],
                    riasec_scores=[],
                ),
                {"thinking": "summary\nPROBE: social_battery - test"},
                ("social_battery", "confidence"),
                ("learning_mode", "confidence"),
            ),
            (
                "purpose",
                purpose_reopen_invalidator_node,
                "purpose",
                "university",
                PurposeProfile(
                    done=True,
                    core_desire=_field(0.91, "freedom"),
                    work_relationship=_field(0.91, "calling"),
                    ai_stance=_field(0.91, "leverage"),
                    location_vision=_field(0.91, "remote"),
                    risk_philosophy=_field(0.91, "startup risk"),
                    key_quote=_field(0.91, "I want freedom"),
                ),
                {"purpose": "summary\nPROBE: risk_philosophy - test"},
                ("risk_philosophy", "confidence"),
                ("core_desire", "confidence"),
            ),
            (
                "goals",
                goals_reopen_invalidator_node,
                "goals",
                "university",
                GoalsProfile(
                    done=True,
                    long=GoalsLongProfile(
                        done=True,
                        income_target=_field(0.91, "$5k"),
                        autonomy_level=_field(0.91, "full"),
                        ownership_model=_field(0.91, "founder"),
                        team_size=_field(0.91, "small"),
                    ),
                    short=GoalsShortProfile(
                        done=True,
                        skill_targets=_field(0.91, "ship"),
                        portfolio_goal=_field(0.91, "2 apps"),
                        credential_needed=_field(0.91, "degree"),
                    ),
                ),
                {"goals": "summary\nPROBE: income_target - test"},
                ("long", "income_target", "confidence"),
                ("short", "skill_targets", "confidence"),
            ),
            (
                "job",
                job_reopen_invalidator_node,
                "job",
                "university",
                JobProfile(
                    done=True,
                    role_category=_field(0.91, "engineer"),
                    company_stage=_field(0.91, "startup"),
                    day_to_day=_field(0.91, "building"),
                    autonomy_level=_field(0.91, "full"),
                ),
                {"job": "summary\nPROBE: role_category - test"},
                ("role_category", "confidence"),
                ("day_to_day", "confidence"),
            ),
            (
                "major",
                major_reopen_invalidator_node,
                "major",
                "university",
                MajorProfile(
                    done=True,
                    field=_field(0.91, "computer science"),
                    curriculum_style=_field(0.91, "project-based"),
                    required_skills_coverage=_field(0.91, "strong"),
                ),
                {"major": "summary\nPROBE: field - test"},
                ("field", "confidence"),
                ("curriculum_style", "confidence"),
            ),
            (
                "university",
                uni_reopen_invalidator_node,
                "university",
                "purpose",
                UniProfile(
                    done=True,
                    prestige_requirement=_field(0.91, "mid-tier"),
                    target_school=_field(0.91, "RMIT"),
                    campus_format=_field(0.91, "international"),
                    is_domestic=False,
                ),
                {"uni": "summary\nPROBE: target_school - test"},
                ("target_school", "confidence"),
                ("prestige_requirement", "confidence"),
            ),
        ]

        for stage_name, node, profile_key, current_stage, profile, reasoning, target_path, untouched_path in cases:
            with self.subTest(stage_name=stage_name):
                state = {
                    profile_key: profile,
                    "stage_transitioned": True,
                    "stage": {
                        "current_stage": current_stage,
                        "anchor_mode": "revisit",
                        "anchor_stage": stage_name,
                    },
                    "stage_reasoning": reasoning,
                }

                updates = node(state)
                updated = updates[profile_key]

                self.assertEqual(_get_nested(updated, target_path), REOPEN_CONFIDENCE_CEILING)
                self.assertEqual(_get_nested(updated, untouched_path), 0.91)
                self.assertFalse(updated["done"])

    def test_retrieval_route_after_planner_requires_need_and_query_across_graphs(self):
        cases = [
            ("job", job_route_after_planner, "job_research", "job_researcher", "job_synthesizer"),
            ("major", major_route_after_planner, "major_research", "major_researcher", "major_synthesizer"),
            ("university", uni_route_after_planner, "uni_research", "uni_researcher", "uni_synthesizer"),
        ]

        for stage_name, router, state_key, expected_yes, expected_no in cases:
            with self.subTest(stage_name=stage_name, branch="researcher"):
                self.assertEqual(
                    router({state_key: {"need_research": True, "search_query": "real query"}}),
                    expected_yes,
                )
            with self.subTest(stage_name=stage_name, branch="missing_query"):
                self.assertEqual(
                    router({state_key: {"need_research": True, "search_query": ""}}),
                    expected_no,
                )
            with self.subTest(stage_name=stage_name, branch="not_needed"):
                self.assertEqual(
                    router({state_key: {"need_research": False, "search_query": "real query"}}),
                    expected_no,
                )


if __name__ == "__main__":
    unittest.main()
