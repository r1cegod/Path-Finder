import copy
import unittest

from backend.data.state import DEFAULT_STATE
from backend.uni_graph import get_uni_research, route_after_planner


class UniGraphContractTest(unittest.TestCase):
    def test_missing_uni_research_defaults_cleanly(self) -> None:
        state = copy.deepcopy(DEFAULT_STATE)

        packet = get_uni_research(state)

        self.assertFalse(packet.need_research)
        self.assertEqual(packet.search_query, "")

    def test_route_after_planner_uses_researcher_when_query_exists(self) -> None:
        state = copy.deepcopy(DEFAULT_STATE)
        state["uni_research"] = {
            "need_research": True,
            "search_query": "hoc phi RMIT Vietnam nganh marketing 2025",
        }

        self.assertEqual(route_after_planner(state), "uni_researcher")

    def test_route_after_planner_skips_researcher_without_query(self) -> None:
        state = copy.deepcopy(DEFAULT_STATE)
        state["uni_research"] = {
            "need_research": False,
            "search_query": "",
        }

        self.assertEqual(route_after_planner(state), "uni_synthesizer")


if __name__ == "__main__":
    unittest.main()
