import unittest

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage

from backend.message_window import append_with_fractional_prune


class MessageWindowContractTest(unittest.TestCase):
    def test_append_without_overflow_only_appends_new_message(self):
        existing = [HumanMessage(content="one"), AIMessage(content="two")]
        new_message = HumanMessage(content="three")

        patch = append_with_fractional_prune(existing, new_message, token_budget=1000)

        self.assertEqual(len(patch), 1)
        self.assertEqual(patch[0].content, "three")

    def test_append_with_overflow_drops_oldest_three_quarters(self):
        existing = [
            HumanMessage(content="x " * 80),
            AIMessage(content="y " * 80),
            HumanMessage(content="z " * 80),
            AIMessage(content="q " * 80),
        ]
        new_message = HumanMessage(content="tail")

        patch = append_with_fractional_prune(existing, new_message, token_budget=50)

        removals = [item for item in patch if isinstance(item, RemoveMessage)]
        appended = [item for item in patch if not isinstance(item, RemoveMessage)]

        self.assertEqual(len(removals), 3)
        self.assertEqual(appended[0].content, "tail")


if __name__ == "__main__":
    unittest.main()
