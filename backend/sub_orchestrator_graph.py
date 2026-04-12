import json
import os
import re
from operator import add
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict

from backend.data.prompts.sub_orchestrator import (
    build_user_tag_bool_reasoning_prompt,
    build_user_tag_summary_prompt,
    build_user_tag_text_prompt,
)
from backend.data.state import (
    MessageTag,
    PathFinderState,
    UserTag,
    UserTagSummaries,
)
from backend.message_window import (
    ROUTING_MEMORY_TOKEN_BUDGET,
    build_fractional_prune_plan,
)

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


class BoolReasoningOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    flag: bool
    reasoning: str


class TextOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str


class SubOrchestratorState(TypedDict):
    messages: list
    routing_memory: list
    retired_routing_memory: list
    routing_memory_updates: list
    routing_memory_over_limit: bool
    message_tag: MessageTag | dict | None
    user_tag: UserTag | dict | None
    user_tag_summaries: UserTagSummaries | dict | None
    turn_count: int
    compliance_turns: int
    disengagement_turns: int
    avoidance_turns: int
    vague_turns: int
    selected_agents: list[str]
    patches: Annotated[list[dict], add]
    summary_patches: Annotated[list[dict], add]


FocusTarget = Literal["summarizer", "worker"]


_llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0.2, max_tokens=450)
_bool_reasoning_llm = _llm.with_structured_output(BoolReasoningOutput, method="function_calling")
_text_llm = _llm.with_structured_output(TextOutput, method="function_calling")
_summary_llm = _llm.with_structured_output(TextOutput, method="function_calling")

BOOL_REASONING_FIELDS = {
    "parental_pressure": "parental_pressure_reasoning",
    "burnout_risk": "burnout_risk_reasoning",
    "urgency": "urgency_reasoning",
    "core_tension": "core_tension_reasoning",
    "reality_gap": "reality_gap_reasoning",
}

TEXT_FIELDS = {
    "self_authorship": "self_authorship",
    "compliance": "compliance_reasoning",
    "disengagement": "disengagement_reasoning",
    "avoidance": "avoidance_reasoning",
    "vague": "vague_reasoning",
}

SUMMARY_FIELDS = [
    "parental_pressure",
    "burnout_risk",
    "urgency",
    "core_tension",
    "reality_gap",
    "self_authorship",
    "compliance",
    "disengagement",
    "avoidance",
    "vague",
]

SUMMARY_NODE_NAMES = {field_name: f"summary_{field_name}" for field_name in SUMMARY_FIELDS}

WORKER_MEMORY_TOKEN_BUDGET = 2500
WORKER_MEMORY_PRESERVE_TAIL = 2


def _coerce_user_tag(raw) -> UserTag:
    if isinstance(raw, UserTag):
        return raw
    if isinstance(raw, dict):
        return UserTag(**raw)
    return UserTag()


def _coerce_user_tag_summaries(raw) -> UserTagSummaries:
    if isinstance(raw, UserTagSummaries):
        return raw
    if isinstance(raw, dict):
        return UserTagSummaries(**raw)
    return UserTagSummaries()


def _coerce_message_tag(raw) -> MessageTag:
    if isinstance(raw, MessageTag):
        return raw
    if isinstance(raw, dict):
        return MessageTag(**raw)
    return MessageTag()


def _unwrap_text_payload(raw: str) -> str:
    if not isinstance(raw, str):
        return str(raw).strip()
    stripped = raw.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return stripped

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped

    if isinstance(parsed, dict) and isinstance(parsed.get("value"), str):
        return parsed["value"].strip()
    return stripped


def _sanitize_generated_text(raw: str) -> str:
    text = _unwrap_text_payload(raw)
    text = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", text)
    text = re.sub(r"[\u4e00-\u9fff\u3400-\u4dbf]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _every_five(turn_count: int) -> bool:
    return turn_count > 0 and turn_count % 5 == 0


def _select_user_tag_agents(state: SubOrchestratorState) -> list[str]:
    tag = _coerce_user_tag(state.get("user_tag"))
    message_tag = _coerce_message_tag(state.get("message_tag"))
    message_type = message_tag.message_type
    every_five = _every_five(state.get("turn_count") or 0)
    selected: list[str] = []

    if tag.parental_pressure or every_five:
        selected.append("parental_pressure")
    if tag.burnout_risk or every_five:
        selected.append("burnout_risk")
    if tag.urgency or every_five:
        selected.append("urgency")
    if tag.core_tension or every_five:
        selected.append("core_tension")
    if tag.reality_gap or every_five:
        selected.append("reality_gap")

    if every_five:
        selected.append("self_authorship")

    if (
        message_type == "compliance"
        or (state.get("compliance_turns") or 0) >= 2
        or every_five
    ):
        selected.append("compliance")

    if (
        message_type == "disengaged"
        or (state.get("disengagement_turns") or 0) >= 2
        or (every_five and bool(tag.disengagement_reasoning))
    ):
        selected.append("disengagement")
    if (
        message_type == "avoidance"
        or (state.get("avoidance_turns") or 0) >= 2
        or (every_five and bool(tag.avoidance_reasoning))
    ):
        selected.append("avoidance")
    if (
        message_type == "vague"
        or (state.get("vague_turns") or 0) >= 2
        or (every_five and bool(tag.vague_reasoning))
    ):
        selected.append("vague")

    return selected


def _should_refresh_summary(state: SubOrchestratorState, field_name: str) -> bool:
    tag = _coerce_user_tag(state.get("user_tag"))
    summaries = _coerce_user_tag_summaries(state.get("user_tag_summaries"))
    message_tag = _coerce_message_tag(state.get("message_tag"))
    message_type = message_tag.message_type

    if field_name in BOOL_REASONING_FIELDS:
        return bool(getattr(tag, field_name)) or bool(getattr(summaries, field_name))
    if field_name == "self_authorship":
        return True
    if field_name == "compliance":
        return (
            message_type == "compliance"
            or (state.get("compliance_turns") or 0) >= 2
            or bool(summaries.compliance)
        )
    if field_name == "disengagement":
        return (
            message_type == "disengaged"
            or (state.get("disengagement_turns") or 0) >= 2
            or bool(summaries.disengagement)
        )
    if field_name == "avoidance":
        return (
            message_type == "avoidance"
            or (state.get("avoidance_turns") or 0) >= 2
            or bool(summaries.avoidance)
        )
    if field_name == "vague":
        return (
            message_type == "vague"
            or (state.get("vague_turns") or 0) >= 2
            or bool(summaries.vague)
        )
    return False


def _limit_check_node(state: SubOrchestratorState) -> dict:
    over_limit, retired, kept, removals = build_fractional_prune_plan(
        state.get("routing_memory") or [],
        ROUTING_MEMORY_TOKEN_BUDGET,
    )
    return {
        "routing_memory_over_limit": over_limit,
        "retired_routing_memory": retired,
        "routing_memory": kept,
        "routing_memory_updates": removals,
        "patches": [],
        "summary_patches": [],
        "selected_agents": [],
    }


def _route_after_limit_check(state: SubOrchestratorState) -> str:
    if state.get("routing_memory_over_limit"):
        return SUMMARY_NODE_NAMES[SUMMARY_FIELDS[0]]
    return "router"


def _route_after_limit_check_for_summarizer(state: SubOrchestratorState) -> str:
    if state.get("routing_memory_over_limit"):
        return SUMMARY_NODE_NAMES[SUMMARY_FIELDS[0]]
    return "merge_summaries"


def _summary_worker(field_name: str):
    def _worker(state: SubOrchestratorState) -> dict:
        if not _should_refresh_summary(state, field_name):
            return {"summary_patches": []}

        tag = _coerce_user_tag(state.get("user_tag"))
        summaries = _coerce_user_tag_summaries(state.get("user_tag_summaries"))
        message_tag = _coerce_message_tag(state.get("message_tag"))
        response = _summary_llm.invoke(
            [SystemMessage(content=build_user_tag_summary_prompt(
                field_name=field_name,
                current_summary=getattr(summaries, field_name),
                message_tag=message_tag.model_dump(),
                user_tag=tag.model_dump(),
            ))] + (state.get("retired_routing_memory") or [])
        )
        return {"summary_patches": [{field_name: _sanitize_generated_text(response.value)}]}

    return _worker


def _merge_summaries_node(state: SubOrchestratorState) -> dict:
    merged = _coerce_user_tag_summaries(state.get("user_tag_summaries")).model_dump()
    for patch in state.get("summary_patches", []):
        merged.update(patch)
    return {
        "user_tag_summaries": merged,
        "summary_patches": [],
        "retired_routing_memory": [],
    }


def _select_worker_memory(state: SubOrchestratorState) -> list:
    routing_memory = state.get("routing_memory") or state.get("messages", [])
    _, _, kept, _ = build_fractional_prune_plan(
        routing_memory,
        WORKER_MEMORY_TOKEN_BUDGET,
        preserve_tail=WORKER_MEMORY_PRESERVE_TAIL,
    )
    return kept


def _router_node(state: SubOrchestratorState) -> dict:
    return {
        "patches": [],
        "selected_agents": _select_user_tag_agents(state),
    }


def _route_selected_agents(state: SubOrchestratorState):
    selected = state.get("selected_agents") or _select_user_tag_agents(state)
    return selected if selected else "merge"


def _bool_reasoning_worker(field_name: str):
    reasoning_field = BOOL_REASONING_FIELDS[field_name]

    def _worker(state: SubOrchestratorState) -> dict:
        tag = _coerce_user_tag(state.get("user_tag"))
        summaries = _coerce_user_tag_summaries(state.get("user_tag_summaries"))
        message_tag = _coerce_message_tag(state.get("message_tag"))
        response = _bool_reasoning_llm.invoke(
            [SystemMessage(content=build_user_tag_bool_reasoning_prompt(
                field_name=field_name,
                current_bool=getattr(tag, field_name),
                current_reasoning=getattr(tag, reasoning_field),
                field_summary=getattr(summaries, field_name),
                message_tag=message_tag.model_dump(),
                user_tag=tag.model_dump(),
            ))] + _select_worker_memory(state)
        )
        return {"patches": [{field_name: response.flag, reasoning_field: response.reasoning}]}

    return _worker


def _text_worker(field_name: str):
    target_field = TEXT_FIELDS[field_name]

    def _worker(state: SubOrchestratorState) -> dict:
        tag = _coerce_user_tag(state.get("user_tag"))
        summaries = _coerce_user_tag_summaries(state.get("user_tag_summaries"))
        message_tag = _coerce_message_tag(state.get("message_tag"))
        response = _text_llm.invoke(
            [SystemMessage(content=build_user_tag_text_prompt(
                field_name=target_field,
                current_value=getattr(tag, target_field),
                field_summary=getattr(summaries, field_name),
                message_tag=message_tag.model_dump(),
                user_tag=tag.model_dump(),
                compliance_turns=state.get("compliance_turns") or 0,
                disengagement_turns=state.get("disengagement_turns") or 0,
                avoidance_turns=state.get("avoidance_turns") or 0,
                vague_turns=state.get("vague_turns") or 0,
            ))] + _select_worker_memory(state)
        )
        return {"patches": [{target_field: _sanitize_generated_text(response.value)}]}

    return _worker


def _merge_node(state: SubOrchestratorState) -> dict:
    merged = _coerce_user_tag(state.get("user_tag")).model_dump()
    for patch in state.get("patches", []):
        merged.update(patch)
    return {"user_tag": merged, "patches": []}


def _build_summary_chain(builder: StateGraph):
    builder.add_node("merge_summaries", _merge_summaries_node)
    for field_name in SUMMARY_FIELDS:
        builder.add_node(SUMMARY_NODE_NAMES[field_name], _summary_worker(field_name))

    for index, field_name in enumerate(SUMMARY_FIELDS):
        current = SUMMARY_NODE_NAMES[field_name]
        if index == len(SUMMARY_FIELDS) - 1:
            builder.add_edge(current, "merge_summaries")
        else:
            builder.add_edge(current, SUMMARY_NODE_NAMES[SUMMARY_FIELDS[index + 1]])


def _build_worker_chain(builder: StateGraph):
    builder.add_node("router", _router_node)
    builder.add_node("merge", _merge_node)

    for field_name in BOOL_REASONING_FIELDS:
        builder.add_node(field_name, _bool_reasoning_worker(field_name))

    for field_name in TEXT_FIELDS:
        builder.add_node(field_name, _text_worker(field_name))

    builder.add_conditional_edges(
        "router",
        _route_selected_agents,
        [*BOOL_REASONING_FIELDS.keys(), *TEXT_FIELDS.keys(), "merge"],
    )

    for field_name in [*BOOL_REASONING_FIELDS.keys(), *TEXT_FIELDS.keys()]:
        builder.add_edge(field_name, "merge")


def _compile_full_graph():
    builder = StateGraph(SubOrchestratorState)
    builder.add_node("limit_check", _limit_check_node)
    _build_summary_chain(builder)
    _build_worker_chain(builder)

    builder.add_edge(START, "limit_check")
    builder.add_conditional_edges(
        "limit_check",
        _route_after_limit_check,
        [SUMMARY_NODE_NAMES[SUMMARY_FIELDS[0]], "router"],
    )
    builder.add_edge("merge_summaries", "router")
    builder.add_edge("merge", END)
    return builder.compile()


def _compile_summarizer_focus_graph():
    builder = StateGraph(SubOrchestratorState)
    builder.add_node("limit_check", _limit_check_node)
    _build_summary_chain(builder)

    builder.add_edge(START, "limit_check")
    builder.add_conditional_edges(
        "limit_check",
        _route_after_limit_check_for_summarizer,
        [SUMMARY_NODE_NAMES[SUMMARY_FIELDS[0]], "merge_summaries"],
    )
    builder.add_edge("merge_summaries", END)
    return builder.compile()


def _compile_worker_focus_graph():
    builder = StateGraph(SubOrchestratorState)
    _build_worker_chain(builder)
    builder.add_edge(START, "router")
    builder.add_edge("merge", END)
    return builder.compile()


_sub_orchestrator_graph = _compile_full_graph()
_sub_orchestrator_summarizer_focus_graph = _compile_summarizer_focus_graph()
_sub_orchestrator_worker_focus_graph = _compile_worker_focus_graph()


def _build_sub_orchestrator_input(state: PathFinderState | dict) -> SubOrchestratorState:
    return {
        "messages": list(state.get("messages") or []),
        "routing_memory": list(state.get("routing_memory") or []),
        "retired_routing_memory": [],
        "routing_memory_updates": [],
        "routing_memory_over_limit": False,
        "message_tag": state.get("message_tag"),
        "user_tag": state.get("user_tag"),
        "user_tag_summaries": state.get("user_tag_summaries"),
        "turn_count": state.get("turn_count") or 0,
        "compliance_turns": state.get("compliance_turns") or 0,
        "disengagement_turns": state.get("disengagement_turns") or 0,
        "avoidance_turns": state.get("avoidance_turns") or 0,
        "vague_turns": state.get("vague_turns") or 0,
        "selected_agents": [],
        "patches": [],
        "summary_patches": [],
    }


def run_sub_orchestrator(state: PathFinderState | dict) -> dict:
    return _sub_orchestrator_graph.invoke(_build_sub_orchestrator_input(state))


def run_sub_orchestrator_focus(state: PathFinderState | dict, target: FocusTarget) -> dict:
    graph = {
        "summarizer": _sub_orchestrator_summarizer_focus_graph,
        "worker": _sub_orchestrator_worker_focus_graph,
    }[target]
    return graph.invoke(_build_sub_orchestrator_input(state))


def sub_orchestrator_node(state: PathFinderState) -> dict:
    result = run_sub_orchestrator(state)
    return {
        "user_tag": result["user_tag"],
        "user_tag_summaries": result.get("user_tag_summaries"),
        "routing_memory": result.get("routing_memory_updates") or [],
    }
