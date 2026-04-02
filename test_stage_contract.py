import unittest

from backend.data.contracts.stages import (
    STAGE_ORDER,
    STAGE_TO_PROFILE_KEY,
    STAGE_TO_QUEUE_KEY,
    STAGE_TO_REASONING_KEY,
)
from backend.data.state import DEFAULT_STATE, StageReasoning


class StageContractTest(unittest.TestCase):
    def test_stage_contract_is_complete(self):
        for stage_name in STAGE_ORDER:
            self.assertIn(stage_name, STAGE_TO_PROFILE_KEY)
            self.assertIn(stage_name, STAGE_TO_REASONING_KEY)
            self.assertIn(stage_name, STAGE_TO_QUEUE_KEY)

    def test_stage_contract_points_to_live_state_keys(self):
        reasoning = StageReasoning()

        for stage_name in STAGE_ORDER:
            self.assertIn(STAGE_TO_PROFILE_KEY[stage_name], DEFAULT_STATE)
            self.assertIn(STAGE_TO_QUEUE_KEY[stage_name], DEFAULT_STATE)
            self.assertTrue(hasattr(reasoning, STAGE_TO_REASONING_KEY[stage_name]))

    def test_stage_contract_values_are_unique(self):
        self.assertEqual(len(STAGE_ORDER), len(set(STAGE_ORDER)))
        self.assertEqual(len(STAGE_ORDER), len(set(STAGE_TO_PROFILE_KEY.values())))
        self.assertEqual(len(STAGE_ORDER), len(set(STAGE_TO_QUEUE_KEY.values())))
        self.assertEqual(len(STAGE_ORDER), len(set(STAGE_TO_REASONING_KEY.values())))


if __name__ == "__main__":
    unittest.main()
