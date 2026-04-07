import copy

from backend.data.state import DEFAULT_STATE
from backend.uni_graph import get_uni_research, route_after_planner


def test_missing_uni_research_defaults_cleanly() -> None:
    state = copy.deepcopy(DEFAULT_STATE)

    packet = get_uni_research(state)

    assert packet.need_research is False
    assert packet.search_query == ""


def test_route_after_planner_uses_researcher_when_query_exists() -> None:
    state = copy.deepcopy(DEFAULT_STATE)
    state["uni_research"] = {
        "need_research": True,
        "search_query": "hoc phi RMIT Vietnam nganh marketing 2025",
    }

    assert route_after_planner(state) == "uni_researcher"


def test_route_after_planner_skips_researcher_without_query() -> None:
    state = copy.deepcopy(DEFAULT_STATE)
    state["uni_research"] = {
        "need_research": False,
        "search_query": "",
    }

    assert route_after_planner(state) == "uni_synthesizer"
