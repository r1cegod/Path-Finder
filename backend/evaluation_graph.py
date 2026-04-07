from __future__ import annotations

import copy
import os

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from backend.data.contracts.stages import STAGE_TO_QUEUE_KEY, StageName
from backend.data.state import DEFAULT_STAGE, PathFinderState
from backend.goals_graph import goals_graph
from backend.job_graph import job_graph
from backend.major_graph import major_graph
from backend.output_graph import context_compiler, output_compiler
from backend.purpose_graph import purpose_graph
from backend.thinking_graph import thinking_graph
from backend.uni_graph import uni_graph

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


def normalize_evaluation_state(stage_name: StageName, state: PathFinderState) -> dict:
    updates: dict = {}
    queue_key = STAGE_TO_QUEUE_KEY[stage_name]
    stage_queue = list(state.get(queue_key) or [])
    messages = list(state.get("messages") or [])

    if not messages and stage_queue:
        updates["messages"] = stage_queue

    stage_raw = state.get("stage") or {}
    stage_state = copy.deepcopy(stage_raw if isinstance(stage_raw, dict) else DEFAULT_STAGE)
    stage_changed = False

    if not stage_state.get("stage_related"):
        stage_state["stage_related"] = [stage_name]
        stage_changed = True

    if not stage_state.get("current_stage"):
        stage_state["current_stage"] = stage_name
        stage_changed = True

    if stage_changed:
        updates["stage"] = stage_state

    return updates


def evaluation_prep_factory(stage_name: StageName):
    def evaluation_prep(state: PathFinderState) -> dict:
        return normalize_evaluation_state(stage_name, state)

    evaluation_prep.__name__ = f"{stage_name}_evaluation_prep"
    return evaluation_prep


def build_stage_evaluation_graph(stage_name: StageName, compiled_stage_graph):
    builder = StateGraph(PathFinderState)
    builder.add_node("evaluation_prep", evaluation_prep_factory(stage_name))
    builder.add_node(stage_name, compiled_stage_graph)
    builder.add_node("context_compiler", context_compiler)
    builder.add_node("output_compiler", output_compiler)
    builder.add_edge(START, "evaluation_prep")
    builder.add_edge("evaluation_prep", stage_name)
    builder.add_edge(stage_name, "context_compiler")
    builder.add_edge("context_compiler", "output_compiler")
    builder.add_edge("output_compiler", END)
    return builder.compile()


thinking_eval_graph = build_stage_evaluation_graph("thinking", thinking_graph)
purpose_eval_graph = build_stage_evaluation_graph("purpose", purpose_graph)
goals_eval_graph = build_stage_evaluation_graph("goals", goals_graph)
job_eval_graph = build_stage_evaluation_graph("job", job_graph)
major_eval_graph = build_stage_evaluation_graph("major", major_graph)
university_eval_graph = build_stage_evaluation_graph("university", uni_graph)
uni_eval_graph = university_eval_graph
