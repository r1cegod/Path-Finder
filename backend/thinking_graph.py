from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os
from backend.data.state import PathFinderState, ThinkingProfile, StageReasoning
from backend.data.contracts.confidence import DONE_CONFIDENCE_THRESHOLD
from backend.data.prompts.thinking import THINKING_DRILL_PROMPT, CONFIDENT_PROMPT
from backend.data.contracts.stages import (
    STAGE_TO_PROFILE_KEY,
    STAGE_TO_QUEUE_KEY,
    STAGE_TO_REASONING_KEY,
)
from backend.stage_profile_utils import apply_reopen_invalidation, normalize_stage_profile

#prep
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

#contract prep
STAGE = "thinking"
PROFILE_KEY = STAGE_TO_PROFILE_KEY[STAGE]
QUEUE_KEY = STAGE_TO_QUEUE_KEY[STAGE]
REASONING_KEY = STAGE_TO_REASONING_KEY[STAGE]

# dict to object
def get_stage_reasoning(state: PathFinderState) -> StageReasoning:
    raw = state.get("stage_reasoning") or {}
    if isinstance(raw, dict):
        return StageReasoning(**raw)
    return raw

def get_thinking_profile(state: PathFinderState) -> ThinkingProfile | None:
    raw = state.get(PROFILE_KEY)
    if isinstance(raw, dict):
        return ThinkingProfile(**raw)
    return raw


def get_current_stage(state: PathFinderState) -> str:
    stage_raw = state.get("stage") or {}
    if isinstance(stage_raw, dict):
        return stage_raw.get("anchor_stage") or stage_raw.get("current_stage", STAGE)
    return getattr(stage_raw, "anchor_stage", "") or getattr(stage_raw, "current_stage", STAGE)


def _extract_field_meta(field: object) -> tuple[str, float]:
    if field is None:
        return "", 0.0
    if isinstance(field, dict):
        return str(field.get("content", "") or ""), float(field.get("confidence", 0.0) or 0.0)
    return str(getattr(field, "content", "") or ""), float(getattr(field, "confidence", 0.0) or 0.0)


def _message_role(message: object) -> str:
    if isinstance(message, dict):
        return str(message.get("type") or message.get("role") or "").lower()
    return str(getattr(message, "type", "") or getattr(message, "role", "") or "").lower()


def _count_human_turns(messages: list[object]) -> int:
    return sum(1 for message in messages if _message_role(message) in {"human", "user"})


def _clamp_field_confidence(field: object, ceiling: float) -> object:
    current_confidence = float(getattr(field, "confidence", 0.0) or 0.0)
    if current_confidence <= ceiling:
        return field
    return field.model_copy(update={"confidence": ceiling})


def _apply_verification_caps(profile: ThinkingProfile, messages: list[object]) -> ThinkingProfile:
    conversational_fields = [
        "learning_mode",
        "env_constraint",
        "social_battery",
        "personality_type",
    ]
    updates: dict[str, object] = {}

    # Stage 0 high confidence requires the full sequence:
    # student claim -> squeeze -> later defense. One human turn cannot satisfy that.
    if _count_human_turns(messages) < 2:
        for field_name in conversational_fields:
            field = getattr(profile, field_name)
            capped_field = _clamp_field_confidence(field, 0.6)
            if capped_field is not field:
                updates[field_name] = capped_field

    capped = profile.model_copy(update=updates) if updates else profile
    return normalize_stage_profile(STAGE, capped)


def _infer_probe_field(thinking: object) -> str:
    if thinking is None:
        return "learning_mode"

    ordered_fields = [
        "learning_mode",
        "social_battery",
        "env_constraint",
        "personality_type",
    ]

    for field_name in ordered_fields:
        if isinstance(thinking, dict):
            field = thinking.get(field_name)
        else:
            field = getattr(thinking, field_name, None)
        content, confidence = _extract_field_meta(field)
        if confidence <= DONE_CONFIDENCE_THRESHOLD or content in {"", "unclear", "not discussed", "not yet"}:
            return field_name

    return "learning_mode"


def _default_probe_instruction(field_name: str) -> str:
    defaults = {
        "learning_mode": "force a trade-off between abstract understanding and practical execution under a real cost.",
        "social_battery": "force a zero-sum choice between sustained solitude and sustained collaboration under pressure.",
        "env_constraint": "force a choice between freedom and the structure or support they would lose.",
        "personality_type": "force a choice between conflicting operating styles under identical stakes.",
    }
    return defaults.get(field_name, "force a concrete trade-off instead of accepting a vague preference.")


def _strip_legacy_probe_suffix(text: str) -> str:
    lines = [line for line in (text or "").strip().splitlines() if line.strip()]
    while lines and lines[-1].strip().upper().startswith("PROBE:"):
        lines.pop()
    return "\n".join(lines).strip()


def _compose_probe_line(response: "ThinkingAnalysis", is_current_stage: bool, thinking: object) -> str:
    if not is_current_stage:
        return "PROBE: NONE (passive analysis only)"

    field_name = (response.probe_field or "").strip()
    if not field_name or field_name.upper() == "NONE":
        field_name = _infer_probe_field(thinking)

    probe_instruction = (response.probe_instruction or "").strip()
    if probe_instruction.upper().startswith("PROBE:"):
        probe_instruction = probe_instruction.split(":", 1)[1].strip()
    if not probe_instruction or probe_instruction.upper().startswith("NONE"):
        probe_instruction = _default_probe_instruction(field_name)

    probe_tension = (response.probe_tension or "").strip()
    if probe_tension and probe_tension.upper() not in {"NONE", "NO TENSION"}:
        return f"PROBE: {field_name} - {probe_tension} {probe_instruction}"

    return f"PROBE: {field_name} - {probe_instruction}"

# structured outputs
class ThinkingAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thinking_summary: str
    probe_field: str
    probe_tension: str
    probe_instruction: str

class ConfidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thinking: ThinkingProfile

# llm
llm          = ChatOpenAI(model="gpt-5.4-mini")
analysis_llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=450).with_structured_output(
    ThinkingAnalysis,
    method="function_calling",
)
confident_llm = llm.with_structured_output(
    ConfidentOutput,
    method="function_calling",
)

# nodes
def thinking_agent(state: PathFinderState) -> dict:
    messages        = state[QUEUE_KEY]
    stage_reasoning = get_stage_reasoning(state)
    thinking        = get_thinking_profile(state)
    is_current_stage_bool = get_current_stage(state) == STAGE

    response = analysis_llm.invoke(
        [SystemMessage(THINKING_DRILL_PROMPT.format(
            is_current_stage=str(is_current_stage_bool),
            stage_reasoning=getattr(stage_reasoning, REASONING_KEY),
            thinking=thinking or "",
        ))] + messages
    )
    summary_body = _strip_legacy_probe_suffix(response.thinking_summary)
    probe_line = _compose_probe_line(response, is_current_stage_bool, thinking)
    full_summary = f"{summary_body}\n{probe_line}" if summary_body else probe_line

    updated = stage_reasoning.model_copy(update={REASONING_KEY: full_summary})
    return {"stage_reasoning": updated.model_dump()}

def confident_node(state: PathFinderState) -> dict:
    messages = state[QUEUE_KEY]
    thinking = get_thinking_profile(state)

    response = confident_llm.invoke(
        [SystemMessage(CONFIDENT_PROMPT.format(
            thinking=thinking or "",
        ))] + messages
    )
    capped_thinking = _apply_verification_caps(response.thinking, messages)
    normalized = normalize_stage_profile(STAGE, capped_thinking)
    return {PROFILE_KEY: normalized.model_dump()}


def reopen_invalidator_node(state: PathFinderState) -> dict:
    thinking = get_thinking_profile(state)
    if thinking is None:
        return {}
    reopened = apply_reopen_invalidation(state, STAGE, thinking)
    normalized = normalize_stage_profile(STAGE, reopened)
    return {PROFILE_KEY: normalized.model_dump()}

# graph
builder = StateGraph(PathFinderState)
builder.add_node("thinking_agent", thinking_agent)
builder.add_node("confident", confident_node)
builder.add_node("reopen_invalidator", reopen_invalidator_node)
builder.add_edge(START, "confident")
builder.add_edge("confident", "reopen_invalidator")
builder.add_edge("reopen_invalidator", "thinking_agent")
builder.add_edge("thinking_agent", END)
thinking_graph = builder.compile()
