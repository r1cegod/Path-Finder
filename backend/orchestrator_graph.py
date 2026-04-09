from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict
from backend.data.state import PathFinderState, StageCheck, MessageTag, UserTag
from backend.data.prompts.orchestrator import INPUT_PARSER_PROMPT
from backend.sub_orchestrator_graph import sub_orchestrator_node
from backend.thinking_graph import thinking_graph
from backend.purpose_graph import purpose_graph
from backend.goals_graph import goals_graph
from backend.job_graph import job_graph
from backend.major_graph import major_graph
from backend.uni_graph import uni_graph
from backend.output_graph import context_compiler, output_compiler
from backend.message_window import append_with_fractional_prune, ROUTING_MEMORY_TOKEN_BUDGET
from backend.data.contracts.stages import (
    STAGE_INDEX,
    STAGE_ORDER,
    STAGE_TO_QUEUE_KEY,
    is_stage_name,
)
from dotenv import load_dotenv
import os

#prep
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
memory = MemorySaver()

#def output
class InputOutputStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bypass_stage: bool
    stage_related: list[str]
    requested_anchor_stage: str
    message_tag: MessageTag
    parental_pressure: bool = False
    burnout_risk: bool = False
    urgency: bool = False
    core_tension: bool = False
    reality_gap: bool = False

#llm
llm = ChatOpenAI(model="gpt-5.4", temperature=0.5)
input_llm = llm.with_structured_output(
    InputOutputStyle,
    method="function_calling",
)

ESCALATION_FAMILY_PRIORITY = {
    "boundary_violation": 0,
    "active_resistance": 1,
    "instability_in_answers": 2,
    "cannot_engage": 3,
    "unknown": 4,
}

PARSER_USER_SIGNAL_FIELDS = {
    "parental_pressure",
    "burnout_risk",
    "urgency",
    "core_tension",
    "reality_gap",
}

def _classify_escalation_reason(raw_reason: str) -> tuple[str, str]:
    prefix = raw_reason.split(":", 1)[0].strip().lower()
    if prefix in {"troll_termination", "troll"}:
        return ("boundary_violation", "troll")
    if prefix in {"avoidance_limit", "avoidance"}:
        return ("active_resistance", "avoidance")
    if prefix in {"contradict_count", "contradict"}:
        return ("instability_in_answers", "contradict")
    if prefix in {"disengagement_limit", "disengagement"}:
        return ("cannot_engage", "disengagement")
    if prefix in {"vague_limit", "vague"}:
        return ("cannot_engage", "vague")
    if prefix in {"compliance"}:
        return ("cannot_engage", "compliance")
    return ("unknown", prefix or "unknown")

def _normalize_escalation_reasons(raw_reasons: list[str]) -> str:
    classified = [
        (*_classify_escalation_reason(raw_reason), raw_reason.strip())
        for raw_reason in raw_reasons
        if raw_reason.strip()
    ]
    if not classified:
        return ""

    primary_family, primary_pattern, _ = min(
        classified,
        key=lambda item: (ESCALATION_FAMILY_PRIORITY.get(item[0], 99), item[1]),
    )
    supporting_patterns = []
    for family, pattern, _ in classified:
        token = f"{family}:{pattern}"
        if token != f"{primary_family}:{primary_pattern}" and token not in supporting_patterns:
            supporting_patterns.append(token)
    supporting_patterns.sort(
        key=lambda token: (
            ESCALATION_FAMILY_PRIORITY.get(token.split(":", 1)[0], 99),
            token,
        )
    )

    lines = [
        f"family: {primary_family}",
        f"primary_pattern: {primary_pattern}",
    ]
    if supporting_patterns:
        lines.append(f"supporting_patterns: {', '.join(supporting_patterns)}")
    lines.append("details:")
    lines.extend(f"- {raw_reason}" for _, _, raw_reason in classified)
    return "\n".join(lines)

#dict to object
def get_stage(state: PathFinderState) -> StageCheck:
    raw = state.get("stage") or {}
    if isinstance(raw, dict):
        return StageCheck(**raw)
    return raw

#nodes
def input_parser(state: PathFinderState):
    stage_got = get_stage(state)
    active_anchor_stage = stage_got.anchor_stage or stage_got.current_stage
    user_tag = state.get("user_tag") or {}
    msg_tag_raw = state.get("message_tag")
    if isinstance(msg_tag_raw, dict):
        prev_msg_tag = MessageTag(**msg_tag_raw)
    elif msg_tag_raw is not None:
        prev_msg_tag = msg_tag_raw
    else:
        prev_msg_tag = None
    prev_message_type = prev_msg_tag.message_type if prev_msg_tag else "null"

    response = input_llm.invoke(
        [SystemMessage(INPUT_PARSER_PROMPT.format(
            user_tag = user_tag,
            current_stage = stage_got.current_stage,
            anchor_stage = active_anchor_stage,
            prev_message_type = prev_message_type,
        ))] + (state.get("messages") or [])
    )
    stage = stage_got.model_copy(update={
        "stage_related": response.stage_related,
        "requested_anchor_stage": response.requested_anchor_stage,
    })
    existing_user_tag = state.get("user_tag")
    if isinstance(existing_user_tag, dict):
        user_tag_model = UserTag(**existing_user_tag)
    elif isinstance(existing_user_tag, UserTag):
        user_tag_model = existing_user_tag
    else:
        user_tag_model = UserTag()

    user_signal_patch = {
        field_name: getattr(response, field_name)
        for field_name in PARSER_USER_SIGNAL_FIELDS
    }

    updates = {
        "bypass_stage": response.bypass_stage,
        "stage": stage.model_dump(),
        "message_tag": response.message_tag.model_dump(),
        "user_tag": user_tag_model.model_copy(update=user_signal_patch).model_dump(),
    }

    #tagger
    if len(state["messages"]) > 0:
        latest_msg = state["messages"][-1]
        updates["routing_memory"] = append_with_fractional_prune(
            state.get("routing_memory") or [],
            latest_msg,
            ROUTING_MEMORY_TOKEN_BUDGET,
        )
        for s in response.stage_related:
            if is_stage_name(s):
                updates[STAGE_TO_QUEUE_KEY[s]] = [latest_msg]

    return updates

def _is_done(profile) -> bool:
    if profile is None:
        return False
    if isinstance(profile, dict):
        return profile.get("done", False)
    return getattr(profile, "done", False)

def stage_manager(state: PathFinderState) -> dict:
    stage = get_stage(state)
    old_contradict_count = state.get("contradict_count") or 0

    user_tag_raw = state.get("user_tag") or {}
    if isinstance(user_tag_raw, dict):
        parental_pressure = user_tag_raw.get("parental_pressure", False)
        burnout_risk      = user_tag_raw.get("burnout_risk", False)
    else:
        parental_pressure = getattr(user_tag_raw, "parental_pressure", False)
        burnout_risk      = getattr(user_tag_raw, "burnout_risk", False)

    prev_stage  = stage.current_stage or "thinking"
    prev_anchor = stage.anchor_stage or prev_stage
    prev_mode   = stage.anchor_mode or "normal"
    current     = prev_stage
    current_idx = STAGE_INDEX.get(current, 0)

    if _is_done(state.get(current)):
        for next_stage in STAGE_ORDER[current_idx + 1:]:
            if not _is_done(state.get(next_stage)):
                current = next_stage
                current_idx = STAGE_INDEX.get(current, 0)
                break

    related = [s for s in stage.stage_related if is_stage_name(s)]
    past   = [s for s in related if STAGE_INDEX.get(s, current_idx) < current_idx]

    requested_target = stage.requested_anchor_stage if is_stage_name(stage.requested_anchor_stage) else ""
    anchor_stage = current
    anchor_mode = "normal"

    if requested_target and requested_target != current:
        anchor_stage = requested_target
        anchor_mode = "revisit" if (_is_done(state.get(requested_target)) or requested_target in past) else "forced"
    elif prev_mode != "normal" and prev_anchor != current:
        if _is_done(state.get(prev_anchor)):
            anchor_stage = current
            anchor_mode = "normal"
        else:
            anchor_stage = prev_anchor
            anchor_mode = prev_mode

    has_contradict = anchor_mode == "normal" and bool(past)

    updated = stage.model_copy(update={
        "current_stage": current,
        "anchor_stage": anchor_stage,
        "anchor_mode": anchor_mode,
        "requested_anchor_stage": "",
        "contradict": has_contradict,
        "contradict_target": past if has_contradict else [],
    })

    new_contradict = old_contradict_count + 1 if has_contradict else max(0, old_contradict_count - 1)

    #path debate check
    bypass_stage = state.get("bypass_stage")
    all_done = all(_is_done(state.get(stage_name)) for stage_name in STAGE_ORDER)
    path_debate_ready = all_done and not parental_pressure and not burnout_risk and bypass_stage

    result = {
        "stage": updated.model_dump(),
        "contradict_count": new_contradict,
        "path_debate_ready": path_debate_ready,
        "stage_transitioned": anchor_stage != prev_anchor,
    }
    return result

def counter_manager(state: PathFinderState) -> dict:
    msg_tag_raw = state.get("message_tag")
    if isinstance(msg_tag_raw, dict):
        msg_tag = MessageTag(**msg_tag_raw)
    elif msg_tag_raw is None:
        return {"turn_count": (state.get("turn_count") or 0) + 1}
    else:
        msg_tag = msg_tag_raw

    msg_type = msg_tag.message_type
    is_troll      = msg_type == "troll"
    is_compliance = msg_type == "compliance"
    is_disengaged = msg_type == "disengaged"
    is_avoidance  = msg_type == "avoidance"
    is_vague      = msg_type == "vague"

    old_troll      = state.get("troll_warnings") or 0
    old_compliance = state.get("compliance_turns") or 0
    old_disengage  = state.get("disengagement_turns") or 0
    old_avoidance  = state.get("avoidance_turns") or 0
    old_vague      = state.get("vague_turns") or 0
    old_turn       = state.get("turn_count") or 0
    old_window     = state.get("trigger_window") or {
        "contradict": 0, "compliance": 0,
        "disengagement": 0, "troll": 0, "avoidance": 0, "vague": 0,
    }

    new_troll      = old_troll + 1      if is_troll      else max(0, old_troll - 1)
    new_compliance = old_compliance + 1 if is_compliance else max(0, old_compliance - 1)
    new_disengage  = old_disengage + 1  if is_disengaged else max(0, old_disengage - 1)
    new_avoidance  = old_avoidance + 1  if is_avoidance  else max(0, old_avoidance - 1)
    new_vague      = old_vague + 1      if is_vague      else max(0, old_vague - 1)
    new_turn       = old_turn + 1

    window = dict(old_window)
    if is_troll:      window["troll"] += 1
    if is_compliance: window["compliance"] += 1
    if is_disengaged: window["disengagement"] += 1
    if is_avoidance:  window["avoidance"] += 1
    if is_vague:      window["vague"] += 1
    stage_raw = state.get("stage") or {}
    if isinstance(stage_raw, dict):
        if stage_raw.get("contradict"): window["contradict"] += 1

    escalation_reasons = []

    contradict_count = state.get("contradict_count") or 0

    if new_troll >= 3:
        escalation_reasons.append("troll_termination: 3 troll warnings")
    if new_disengage >= 4:
        escalation_reasons.append("disengagement_limit: 4 consecutive disengaged turns")
    if new_avoidance >= 4:
        escalation_reasons.append("avoidance_limit: 4 consecutive avoidance turns")
    if new_vague >= 4:
        escalation_reasons.append("vague_limit: 4 consecutive vague turns")
    if contradict_count >= 3:
        escalation_reasons.append("contradict_count: 3 consecutive stage contradictions")

    if new_turn > 0 and new_turn % 10 == 0:
        for key, triggers in window.items():
            if triggers >= 5:
                if key == "compliance":
                    new_compliance = 9
                else:
                    escalation_reasons.append(f"{key}: {triggers}/10 triggers in window")
        window = {k: 0 for k in window}

    #compliance
    if new_compliance >= 10:
        escalation_reasons.append("compliance: chronic pattern, student cannot engage genuinely")


    result = {
        "troll_warnings":      new_troll,
        "compliance_turns":    new_compliance,
        "disengagement_turns": new_disengage,
        "avoidance_turns":     new_avoidance,
        "vague_turns":         new_vague,
        "turn_count":          new_turn,
        "trigger_window":      window,
    }

    if escalation_reasons:
        result["escalation_pending"] = True
        result["escalation_reason"] = _normalize_escalation_reasons(escalation_reasons)

    return result

def route_stage(state: PathFinderState) -> str:
    if state.get("escalation_pending") or state.get("bypass_stage"):
        return "context_compiler"
    stage_raw = state.get("stage") or {}
    active = (stage_raw.get("anchor_stage") if isinstance(stage_raw, dict)
              else getattr(stage_raw, "anchor_stage", "thinking"))
    return active if is_stage_name(active) else "thinking"

#graph
builder = StateGraph(PathFinderState)

#nodess
builder.add_node("input_parser",    input_parser)
builder.add_node("sub_orchestrator", sub_orchestrator_node)
builder.add_node("stage_manager",   stage_manager)
builder.add_node("counter_manager", counter_manager)

builder.add_node("thinking",   thinking_graph)
builder.add_node("purpose",    purpose_graph)
builder.add_node("goals",      goals_graph)
builder.add_node("job",        job_graph)
builder.add_node("major",      major_graph)
builder.add_node("university", uni_graph)

builder.add_node("context_compiler", context_compiler)
builder.add_node("output_compiler",  output_compiler)

builder.add_edge(START, "input_parser")
builder.add_edge("input_parser",    "sub_orchestrator")
builder.add_edge("sub_orchestrator", "stage_manager")
builder.add_edge("stage_manager",   "counter_manager")

#stagerouting
_stage_targets = [*STAGE_ORDER, "context_compiler"]
builder.add_conditional_edges("counter_manager", route_stage, _stage_targets)

for _s in STAGE_ORDER:
    builder.add_edge(_s, "context_compiler")

#outputchain
builder.add_edge("context_compiler", "output_compiler")
builder.add_edge("output_compiler",  END)

input_orchestrator = builder.compile(checkpointer=memory)
