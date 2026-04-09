import unittest

from backend.data.state import FieldEntry, ThinkingProfile
from backend.thinking_graph import _apply_verification_caps


def _build_profile(confidence: float) -> ThinkingProfile:
    return ThinkingProfile(
        done=True,
        learning_mode=FieldEntry(content="theoretical", confidence=confidence),
        env_constraint=FieldEntry(content="home", confidence=confidence),
        social_battery=FieldEntry(content="solo", confidence=confidence),
        personality_type=FieldEntry(content="builder", confidence=confidence),
        brain_type=[],
        riasec_top=[],
        riasec_scores=[],
    )


class ThinkingGraphContractTest(unittest.TestCase):
    def test_single_turn_claims_stay_capped(self) -> None:
        profile = _build_profile(0.96)
        messages = [
            {"role": "assistant", "content": "Choose one."},
            {"role": "user", "content": "I want to work alone in a dark room."},
        ]

        normalized = _apply_verification_caps(profile, messages)

        self.assertEqual(normalized.learning_mode.confidence, 0.6)
        self.assertEqual(normalized.env_constraint.confidence, 0.6)
        self.assertEqual(normalized.social_battery.confidence, 0.6)
        self.assertEqual(normalized.personality_type.confidence, 0.6)
        self.assertFalse(normalized.done)

    def test_multi_turn_defense_can_keep_high_confidence(self) -> None:
        profile = _build_profile(0.85)
        messages = [
            {"role": "assistant", "content": "What do you prefer?"},
            {"role": "user", "content": "I prefer working alone."},
            {"role": "assistant", "content": "Even if the team would help?"},
            {"role": "user", "content": "Yes. I still choose solitude and accept slower progress."},
        ]

        normalized = _apply_verification_caps(profile, messages)

        self.assertEqual(normalized.learning_mode.confidence, 0.85)
        self.assertEqual(normalized.env_constraint.confidence, 0.85)
        self.assertEqual(normalized.social_battery.confidence, 0.85)
        self.assertEqual(normalized.personality_type.confidence, 0.85)
        self.assertTrue(normalized.done)


if __name__ == "__main__":
    unittest.main()
