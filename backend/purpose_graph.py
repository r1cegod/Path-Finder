from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os
from backend.data.state import PathFinderState, PurposeProfile, StageReasoning
from backend.data.prompts.purpose import PURPOSE_DRILL_PROMPT, CONFIDENT_PROMPT
from backend.data.contracts.stages import (
    STAGE_TO_PROFILE_KEY,
    STAGE_TO_QUEUE_KEY,
    STAGE_TO_REASONING_KEY,
)

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# contract prep
STAGE = "purpose"
PROFILE_KEY = STAGE_TO_PROFILE_KEY[STAGE]
QUEUE_KEY = STAGE_TO_QUEUE_KEY[STAGE]
REASONING_KEY = STAGE_TO_REASONING_KEY[STAGE]

# dict to object
def get_stage_reasoning(state: PathFinderState) -> StageReasoning:
    raw = state.get("stage_reasoning") or {}
    if isinstance(raw, dict):
        return StageReasoning(**raw)
    return raw

def get_current_stage(state: PathFinderState) -> str:
    stage_raw = state.get("stage") or {}
    if isinstance(stage_raw, dict):
        return stage_raw.get("current_stage", STAGE)
    return getattr(stage_raw, "current_stage", STAGE)


def _extract_field_meta(field: object) -> tuple[str, float]:
    if field is None:
        return "", 0.0
    if isinstance(field, dict):
        return str(field.get("content", "") or ""), float(field.get("confidence", 0.0) or 0.0)
    return str(getattr(field, "content", "") or ""), float(getattr(field, "confidence", 0.0) or 0.0)


def _infer_probe_field(purpose: object) -> str:
    if purpose is None:
        return "core_desire"

    ordered_fields = [
        "core_desire",
        "risk_philosophy",
        "work_relationship",
        "location_vision",
        "ai_stance",
    ]

    for field_name in ordered_fields:
        if isinstance(purpose, dict):
            field = purpose.get(field_name)
        else:
            field = getattr(purpose, field_name, None)
        content, confidence = _extract_field_meta(field)
        if confidence < 0.7 or content in {"", "unclear", "not discussed", "not yet"}:
            return field_name

    return "core_desire"


def _default_probe_instruction(field_name: str) -> str:
    defaults = {
        "core_desire": "force a choice between the claimed desire and the real cost or sacrifice required to own it.",
        "risk_philosophy": "force a trade-off between stability and upside instead of letting the student keep both.",
        "work_relationship": "force a choice between calling-level devotion and the exit or comfort they still want.",
        "location_vision": "force a choice between geographic freedom and the structure, support, or income they would lose.",
        "ai_stance": "force a choice between convenience use and structural leverage over the work that matters.",
    }
    return defaults.get(field_name, "force a concrete trade-off instead of accepting a vague preference.")


def _strip_legacy_probe_suffix(text: str) -> str:
    # Defensive cleanup: the analyst now returns structured probe fields, but the model can
    # still leak an old-style trailing "PROBE:" line into purpose_summary.
    lines = [line for line in (text or "").strip().splitlines() if line.strip()]
    while lines and lines[-1].strip().upper().startswith("PROBE:"):
        lines.pop()
    return "\n".join(lines).strip()


def _compose_probe_line(response: "PurposeAnalysis", is_current_stage: bool, purpose: object) -> str:
    if not is_current_stage:
        return "PROBE: NONE (passive analysis only)"

    field_name = (response.probe_field or "").strip()
    if not field_name or field_name.upper() == "NONE":
        field_name = _infer_probe_field(purpose)

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
class PurposeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose_summary: str
    probe_field: str
    probe_tension: str
    probe_instruction: str

class ConfidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose: PurposeProfile

# llm
llm          = ChatOpenAI(model="gpt-5.4-mini")
analysis_llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=450).with_structured_output(PurposeAnalysis)
confident_llm = llm.with_structured_output(ConfidentOutput)

# nodes
def purpose_agent(state: PathFinderState) -> dict:
    messages        = state[QUEUE_KEY]
    stage_reasoning = get_stage_reasoning(state)
    purpose         = state.get(PROFILE_KEY)

    thinking    = state.get("thinking")
    message_tag = state.get("message_tag")
    user_tag    = state.get("user_tag")

    is_current_stage_bool = get_current_stage(state) == STAGE

    response = analysis_llm.invoke(
        [SystemMessage(PURPOSE_DRILL_PROMPT.format(
            is_current_stage=str(is_current_stage_bool),
            stage_reasoning=getattr(stage_reasoning, REASONING_KEY),
            purpose=purpose or "",
            thinking=thinking or "",
            message_tag=message_tag or "",
            user_tag=user_tag or "",
        ))] + messages
    )

    summary_body = _strip_legacy_probe_suffix(response.purpose_summary)
    probe_line = _compose_probe_line(response, is_current_stage_bool, purpose)
    full_summary = f"{summary_body}\n{probe_line}" if summary_body else probe_line

    updated = stage_reasoning.model_copy(update={REASONING_KEY: full_summary})
    return {"stage_reasoning": updated.model_dump()}

def confident_node(state: PathFinderState) -> dict:
    messages = state[QUEUE_KEY]
    purpose  = state.get(PROFILE_KEY)

    response = confident_llm.invoke(
        [SystemMessage(CONFIDENT_PROMPT.format(purpose=purpose or ""))] + messages
    )
    return {PROFILE_KEY: response.purpose.model_dump()}

# graph
builder = StateGraph(PathFinderState)
builder.add_node("purpose_agent", purpose_agent)
builder.add_node("confident", confident_node)
builder.add_edge(START, "confident")
builder.add_edge("confident", "purpose_agent")
builder.add_edge("purpose_agent", END)
purpose_graph = builder.compile()
