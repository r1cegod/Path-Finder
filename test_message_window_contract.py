import unittest

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage

from backend.message_window import build_fractional_prune_plan


class MessageWindowContractTest(unittest.TestCase):
    def test_plan_without_overflow_keeps_full_window(self):
        existing = [HumanMessage(content="one"), AIMessage(content="two")]

        over_limit, retired, kept, removals = build_fractional_prune_plan(existing, token_budget=1000)

        self.assertFalse(over_limit)
        self.assertEqual(retired, [])
        self.assertEqual(kept, existing)
        self.assertEqual(removals, [])

    def test_plan_with_overflow_drops_oldest_three_quarters(self):
        existing = [
            HumanMessage(content="x " * 80, id="h1"),
            AIMessage(content="y " * 80, id="a2"),
            HumanMessage(content="z " * 80, id="h3"),
            AIMessage(content="q " * 80, id="a4"),
        ]

        over_limit, retired, kept, removals = build_fractional_prune_plan(existing, token_budget=50)

        self.assertTrue(over_limit)
        self.assertEqual(len(retired), 3)
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(removals), 3)
        self.assertTrue(all(isinstance(item, RemoveMessage) for item in removals))

    def test_plan_can_preserve_latest_message_when_pruning(self):
        existing = [
            HumanMessage(content="x " * 80, id="h1"),
            AIMessage(content="y " * 80, id="a2"),
            HumanMessage(content="z " * 80, id="h3"),
            AIMessage(content="q " * 80, id="a4"),
        ]

        over_limit, retired, kept, removals = build_fractional_prune_plan(
            existing,
            token_budget=50,
            preserve_tail=1,
        )

        self.assertTrue(over_limit)
        self.assertEqual(len(retired), 3)
        self.assertEqual([message.id for message in kept], ["a4"])
        self.assertEqual(len(removals), 3)


if __name__ == "__main__":
    unittest.main()
