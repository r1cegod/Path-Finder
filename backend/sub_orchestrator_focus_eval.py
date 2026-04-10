from __future__ import annotations

import copy
import json
from typing import Any, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

from backend.data.state import DEFAULT_STAGE, DEFAULT_STATE


FocusTarget = Literal["summarizer", "worker"]
FOCUS_META_KEYS = ("eval_case", "expected_checks", "notes")
FOCUS_QUEUE_KEYS = (
    "messages",
    "routing_memory",
    "thinking_style_message",
    "purpose_message",
    "goals_message",
    "job_message",
    "major_message",
    "uni_message",
)


def split_focus_eval_payload(raw_input: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = copy.deepcopy(raw_input)
    metadata: dict[str, Any] = {}
    for key in FOCUS_META_KEYS:
        if key in payload:
            metadata[key] = payload.pop(key)
    return payload, metadata


def build_message(message_data: dict[str, Any], index: int, queue_key: str) -> BaseMessage:
    role = message_data.get("role")
    if role not in {"assistant", "system", "tool", "user"}:
        raise ValueError(
            f"Unsupported role '{role}' in '{queue_key}' at message index {index}. "
            "Expected assistant, system, tool, or user."
        )

    content = message_data.get("content", "")
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False)
    repeat = message_data.get("repeat", 1)
    if repeat != 1:
        if not isinstance(repeat, int) or repeat < 1:
            raise ValueError(f"'{queue_key}' message #{index} has invalid repeat value.")
        content = "\n".join([content] * repeat)

    if role == "assistant":
        return AIMessage(content=content)
    if role == "system":
        return SystemMessage(content=content)
    if role == "tool":
        tool_call_id = str(message_data.get("tool_call_id") or f"{queue_key}-tool-{index}")
        return ToolMessage(content=content, tool_call_id=tool_call_id)
    return HumanMessage(content=content)


def build_message_list(raw_messages: Any, queue_key: str) -> list[BaseMessage]:
    if not isinstance(raw_messages, list):
        raise ValueError(f"'{queue_key}' must be a list of message objects.")

    messages: list[BaseMessage] = []
    for index, message_data in enumerate(raw_messages, start=1):
        if isinstance(message_data, BaseMessage):
            messages.append(message_data)
            continue
        if not isinstance(message_data, dict):
            raise ValueError(f"'{queue_key}' message #{index} must be an object with role/content.")
        messages.append(build_message(message_data, index=index, queue_key=queue_key))
    return messages


def build_focus_eval_state(raw_input: dict[str, Any], target: FocusTarget) -> tuple[dict[str, Any], dict[str, Any]]:
    payload, metadata = split_focus_eval_payload(raw_input)
    state = copy.deepcopy(DEFAULT_STATE)
    state["stage"] = copy.deepcopy(DEFAULT_STAGE)

    for key, value in payload.items():
        if key == "stage":
            if value is None:
                continue
            if not isinstance(value, dict):
                raise ValueError("'stage' must be a JSON object.")
            merged_stage = copy.deepcopy(DEFAULT_STAGE)
            merged_stage.update(copy.deepcopy(value))
            state["stage"] = merged_stage
            continue

        if key in FOCUS_QUEUE_KEYS:
            state[key] = build_message_list(value, queue_key=key)
            continue

        state[key] = copy.deepcopy(value)

    if not state.get("routing_memory") and state.get("messages"):
        state["routing_memory"] = copy.deepcopy(state["messages"])

    if target == "worker" and not state.get("routing_memory"):
        raise ValueError("Worker focus eval requires 'routing_memory' or fallback 'messages'.")

    if target == "summarizer" and not state.get("routing_memory"):
        raise ValueError("Summarizer focus eval requires 'routing_memory' or fallback 'messages'.")

    return state, metadata
