import os
from operator import add
from typing import Annotated, TypedDict

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv

from backend.data.prompts.sub_orchestrator import (
    USER_TAG_BOOL_REASONING_PROMPT,
    USER_TAG_TEXT_PROMPT,
)
from backend.data.state import MessageTag, PathFinderState, UserTag

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
    message_tag: MessageTag | dict | None
    user_tag: UserTag | dict | None
    turn_count: int
    compliance_turns: int
    disengagement_turns: int
    avoidance_turns: int
    vague_turns: int
    patches: Annotated[list[dict], add]


_llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0.0, max_tokens=180)
_bool_reasoning_llm = _llm.with_structured_output(BoolReasoningOutput, method="function_calling")
_text_llm = _llm.with_structured_output(TextOutput, method="function_calling")

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


def _coerce_user_tag(raw) -> UserTag:
    if isinstance(raw, UserTag):
        return raw
    if isinstance(raw, dict):
        return UserTag(**raw)
    return UserTag()


def _coerce_message_tag(raw) -> MessageTag:
    if isinstance(raw, MessageTag):
        return raw
    if isinstance(raw, dict):
        return MessageTag(**raw)
    return MessageTag()


def _every_five(turn_count: int) -> bool:
    return turn_count > 0 and turn_count % 5 == 0


def _select_user_tag_agents(state: SubOrchestratorState) -> list[str]:
    tag = _coerce_user_tag(state.get("user_tag"))
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
        selected.extend(["self_authorship", "compliance"])

    if (state.get("disengagement_turns") or 0) >= 2 or every_five:
        selected.append("disengagement")
    if (state.get("avoidance_turns") or 0) >= 2 or every_five:
        selected.append("avoidance")
    if (state.get("vague_turns") or 0) >= 2 or every_five:
        selected.append("vague")

    return selected


def _router_node(state: SubOrchestratorState) -> dict:
    return {"patches": []}


def _route_agents(state: SubOrchestratorState):
    selected = _select_user_tag_agents(state)
    return selected if selected else "merge"


def _bool_reasoning_worker(field_name: str):
    reasoning_field = BOOL_REASONING_FIELDS[field_name]

    def _worker(state: SubOrchestratorState) -> dict:
        tag = _coerce_user_tag(state.get("user_tag"))
        message_tag = _coerce_message_tag(state.get("message_tag"))
        response = _bool_reasoning_llm.invoke(
            [SystemMessage(content=USER_TAG_BOOL_REASONING_PROMPT.format(
                field_name=field_name,
                current_bool=getattr(tag, field_name),
                current_reasoning=getattr(tag, reasoning_field),
                message_tag=message_tag.model_dump(),
                user_tag=tag.model_dump(),
            ))] + (state.get("routing_memory") or state.get("messages", []))
        )
        return {"patches": [{field_name: response.flag, reasoning_field: response.reasoning}]}

    return _worker


def _text_worker(field_name: str):
    target_field = TEXT_FIELDS[field_name]

    def _worker(state: SubOrchestratorState) -> dict:
        tag = _coerce_user_tag(state.get("user_tag"))
        message_tag = _coerce_message_tag(state.get("message_tag"))
        response = _text_llm.invoke(
            [SystemMessage(content=USER_TAG_TEXT_PROMPT.format(
                field_name=target_field,
                current_value=getattr(tag, target_field),
                message_tag=message_tag.model_dump(),
                user_tag=tag.model_dump(),
                compliance_turns=state.get("compliance_turns") or 0,
                disengagement_turns=state.get("disengagement_turns") or 0,
                avoidance_turns=state.get("avoidance_turns") or 0,
                vague_turns=state.get("vague_turns") or 0,
            ))] + (state.get("routing_memory") or state.get("messages", []))
        )
        return {"patches": [{target_field: response.value}]}

    return _worker


def _merge_node(state: SubOrchestratorState) -> dict:
    merged = _coerce_user_tag(state.get("user_tag")).model_dump()
    for patch in state.get("patches", []):
        merged.update(patch)
    return {"user_tag": merged, "patches": []}


builder = StateGraph(SubOrchestratorState)
builder.add_node("router", _router_node)
builder.add_node("merge", _merge_node)

for field_name in BOOL_REASONING_FIELDS:
    builder.add_node(field_name, _bool_reasoning_worker(field_name))

for field_name in TEXT_FIELDS:
    builder.add_node(field_name, _text_worker(field_name))

builder.add_edge(START, "router")
builder.add_conditional_edges(
    "router",
    _route_agents,
    [*BOOL_REASONING_FIELDS.keys(), *TEXT_FIELDS.keys(), "merge"],
)

for field_name in [*BOOL_REASONING_FIELDS.keys(), *TEXT_FIELDS.keys()]:
    builder.add_edge(field_name, "merge")

builder.add_edge("merge", END)
_sub_orchestrator_graph = builder.compile()


def sub_orchestrator_node(state: PathFinderState) -> dict:
    result = _sub_orchestrator_graph.invoke(
        {
            "messages": state.get("messages") or [],
            "routing_memory": state.get("routing_memory") or [],
            "message_tag": state.get("message_tag"),
            "user_tag": state.get("user_tag"),
            "turn_count": state.get("turn_count") or 0,
            "compliance_turns": state.get("compliance_turns") or 0,
            "disengagement_turns": state.get("disengagement_turns") or 0,
            "avoidance_turns": state.get("avoidance_turns") or 0,
            "vague_turns": state.get("vague_turns") or 0,
            "patches": [],
        }
    )
    return {"user_tag": result["user_tag"]}
