from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os

from backend.data.contracts.research_sources import (
    UNIVERSITY_ADMISSIONS_DOMAINS,
    UNIVERSITY_OFFICIAL_DOMAINS,
)
from backend.data.contracts.confidence import DONE_CONFIDENCE_THRESHOLD
from backend.data.contracts.stages import (
    STAGE_TO_PROFILE_KEY,
    STAGE_TO_QUEUE_KEY,
    STAGE_TO_REASONING_KEY,
)
from backend.data.prompts.uni import (
    UNI_CONFIDENT_PROMPT,
    UNI_RESEARCH_PLAN_PROMPT,
    UNI_SYNTHESIS_PROMPT,
)
from backend.data.state import PathFinderState, StageReasoning, UniProfile, UniResearch
from backend.retrieval import SearchRequest, format_search_response, search_web
from backend.stage_profile_utils import apply_reopen_invalidation, normalize_stage_profile

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


STAGE = "university"
PROFILE_KEY = STAGE_TO_PROFILE_KEY[STAGE]
QUEUE_KEY = STAGE_TO_QUEUE_KEY[STAGE]
REASONING_KEY = STAGE_TO_REASONING_KEY[STAGE]


class ConfidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    university: UniProfile


class UniResearchPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    need_research: bool
    query_focus: str
    contradiction_to_test: str
    search_query: str
    domain_bucket: str


class UniAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    uni_summary: str
    probe_field: str
    probe_tension: str
    probe_instruction: str


planner_llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=300).with_structured_output(
    UniResearchPlan,
    method="function_calling",
)
analysis_llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=450).with_structured_output(
    UniAnalysis,
    method="function_calling",
)
confident_llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=450).with_structured_output(
    ConfidentOutput,
    method="function_calling",
)


def _merge_domains(*groups: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(domain for group in groups for domain in group))


DOMAIN_BUCKETS: dict[str, tuple[str, ...]] = {
    "official_program": UNIVERSITY_OFFICIAL_DOMAINS,
    "admissions": _merge_domains(UNIVERSITY_OFFICIAL_DOMAINS, UNIVERSITY_ADMISSIONS_DOMAINS),
    "tuition_roi": UNIVERSITY_OFFICIAL_DOMAINS,
    "prestige_gate": (),
    "international_reality": (),
    "none": (),
}
VALID_PROBE_FIELDS = {"target_school", "prestige_requirement", "campus_format"}
SCHOOL_DOMAIN_MARKERS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("fpt",), ("fpt.edu.vn",)),
    (("ueh",), ("ueh.edu.vn",)),
    (("uel",), ("uel.edu.vn",)),
    (("rmit",), ("rmit.edu.vn",)),
    (("usth",), ("usth.edu.vn",)),
    (("bach khoa", "hcmut"), ("hcmut.edu.vn",)),
    (("vnu", "dai hoc quoc gia"), ("vnu.edu.vn", "vnuhcm.edu.vn")),
)


def get_stage_reasoning(state: PathFinderState) -> StageReasoning:
    raw = state.get("stage_reasoning") or {}
    if isinstance(raw, dict):
        return StageReasoning(**raw)
    return raw


def get_uni_research(state: PathFinderState) -> UniResearch:
    raw = state.get("uni_research")
    if raw is None:
        return UniResearch()
    if isinstance(raw, dict):
        return UniResearch(**raw)
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


def _infer_probe_field(uni: object) -> str:
    if uni is None:
        return "target_school"

    ordered_fields = [
        "target_school",
        "prestige_requirement",
        "campus_format",
    ]

    for field_name in ordered_fields:
        field = uni.get(field_name) if isinstance(uni, dict) else getattr(uni, field_name, None)
        content, confidence = _extract_field_meta(field)
        if confidence <= DONE_CONFIDENCE_THRESHOLD or content in {"", "unclear", "not discussed", "not yet"}:
            return field_name

    return "target_school"


def _default_probe_instruction(field_name: str) -> str:
    defaults = {
        "target_school": "force the student to defend the exact school against its hardest ROI or admissions barrier.",
        "prestige_requirement": "force a choice between the status fantasy and the job path that actually needs less prestige.",
        "campus_format": "force the student to choose between the desired location format and the cost or visa burden it creates.",
    }
    return defaults.get(field_name, "force one concrete school-choice trade-off instead of vague preference.")


def _strip_legacy_probe_suffix(text: str) -> str:
    lines = [line for line in (text or "").strip().splitlines() if line.strip()]
    while lines and lines[-1].strip().upper().startswith("PROBE:"):
        lines.pop()
    return "\n".join(lines).strip()


def _compose_probe_line(response: UniAnalysis, is_current_stage: bool, uni: object) -> str:
    if not is_current_stage:
        return "PROBE: NONE (passive analysis only)"

    field_name = (response.probe_field or "").strip()
    if field_name not in VALID_PROBE_FIELDS:
        field_name = _infer_probe_field(uni)

    probe_instruction = (response.probe_instruction or "").strip()
    if probe_instruction.upper().startswith("PROBE:"):
        probe_instruction = probe_instruction.split(":", 1)[1].strip()
    if not probe_instruction or probe_instruction.upper().startswith("NONE"):
        probe_instruction = _default_probe_instruction(field_name)

    probe_tension = (response.probe_tension or "").strip()
    if probe_tension and probe_tension.upper() not in {"NONE", "NO TENSION"}:
        return f"PROBE: {field_name} - {probe_tension} {probe_instruction}"

    return f"PROBE: {field_name} - {probe_instruction}"


def _collect_source_urls(response) -> list[str]:
    return [hit.url for hit in response.hits if hit.url]


def _narrow_domains_for_named_school(query: str, allowed_domains: list[str]) -> list[str]:
    if not allowed_domains:
        return allowed_domains

    query_lower = (query or "").lower()
    for markers, domains in SCHOOL_DOMAIN_MARKERS:
        if not any(marker in query_lower for marker in markers):
            continue

        narrowed = [domain for domain in allowed_domains if domain in domains]
        if narrowed:
            return narrowed

    return allowed_domains


def _run_web_research(packet: UniResearch) -> UniResearch:
    bucket = (packet.domain_bucket or "none").strip().lower()
    allowed_domains = _narrow_domains_for_named_school(
        packet.search_query,
        list(DOMAIN_BUCKETS.get(bucket, ())),
    )
    response = search_web(
        SearchRequest(
            query=packet.search_query,
            vertical="general",
            domains_allowlist=allowed_domains,
            max_results=5,
            fetch_mode="extract_top_hits",
        )
    )

    return packet.model_copy(
        update={
            "evidence_summary": format_search_response(response, include_extracted=True),
            "cited_sources": _collect_source_urls(response),
            "research_complete": True,
        }
    )


def confident_node(state: PathFinderState) -> dict:
    messages = state[QUEUE_KEY]
    uni = state.get(PROFILE_KEY)

    response = confident_llm.invoke([SystemMessage(UNI_CONFIDENT_PROMPT.format(
        uni=uni or "",
    ))] + messages)
    return {PROFILE_KEY: response.university.model_dump()}


def reopen_invalidator_node(state: PathFinderState) -> dict:
    raw = state.get(PROFILE_KEY)
    uni = UniProfile(**raw) if isinstance(raw, dict) else raw
    if uni is None:
        return {}
    reopened = apply_reopen_invalidation(state, STAGE, uni)
    normalized = normalize_stage_profile(STAGE, reopened)
    return {PROFILE_KEY: normalized.model_dump()}


def uni_research_planner(state: PathFinderState) -> dict:
    messages = state[QUEUE_KEY]
    stage_reasoning = get_stage_reasoning(state)
    uni = state.get(PROFILE_KEY)
    uni_research = get_uni_research(state)
    thinking = state.get("thinking", {})
    purpose = state.get("purpose", {})
    goals = state.get("goals", {})
    job = state.get("job", {})
    major = state.get("major", {})
    message_tag = state.get("message_tag", {})
    user_tag = state.get("user_tag", {})
    summary = state.get("summary", "")
    is_current_stage = get_current_stage(state) == STAGE

    response = planner_llm.invoke(
        [SystemMessage(UNI_RESEARCH_PLAN_PROMPT.format(
            is_current_stage=is_current_stage,
            stage_reasoning=getattr(stage_reasoning, REASONING_KEY),
            uni=uni or "",
            uni_research=uni_research.model_dump(),
            thinking=thinking or "",
            purpose=purpose or "",
            goals=goals or "",
            job=job or "",
            major=major or "",
            message_tag=message_tag or "",
            user_tag=user_tag or "",
            summary=summary,
        ))] + messages
    )

    packet = UniResearch(
        need_research=response.need_research and bool((response.search_query or "").strip()),
        query_focus=(response.query_focus or "").strip(),
        contradiction_to_test=(response.contradiction_to_test or "").strip(),
        search_query=(response.search_query or "").strip(),
        domain_bucket=((response.domain_bucket or "none").strip().lower()),
        evidence_summary="",
        cited_sources=[],
        market_verdict="",
        research_complete=False,
    )

    return {"uni_research": packet.model_dump()}


def uni_researcher(state: PathFinderState) -> dict:
    packet = get_uni_research(state)
    if not packet.need_research or not packet.search_query:
        return {"uni_research": packet.model_copy(update={"research_complete": False}).model_dump()}

    researched = _run_web_research(packet)
    return {"uni_research": researched.model_dump()}


def uni_synthesizer(state: PathFinderState) -> dict:
    messages = state[QUEUE_KEY]
    stage_reasoning = get_stage_reasoning(state)
    uni = state.get(PROFILE_KEY)
    uni_research = get_uni_research(state)
    thinking = state.get("thinking", {})
    purpose = state.get("purpose", {})
    goals = state.get("goals", {})
    job = state.get("job", {})
    major = state.get("major", {})
    message_tag = state.get("message_tag", {})
    user_tag = state.get("user_tag", {})
    summary = state.get("summary", "")
    is_current_stage = get_current_stage(state) == STAGE

    response = analysis_llm.invoke(
        [SystemMessage(UNI_SYNTHESIS_PROMPT.format(
            is_current_stage=str(is_current_stage),
            stage_reasoning=getattr(stage_reasoning, REASONING_KEY),
            uni=uni or "",
            uni_research=uni_research.model_dump(),
            thinking=thinking or "",
            purpose=purpose or "",
            goals=goals or "",
            job=job or "",
            major=major or "",
            message_tag=message_tag or "",
            user_tag=user_tag or "",
            summary=summary,
        ))] + messages
    )

    summary_body = _strip_legacy_probe_suffix(response.uni_summary)
    probe_line = _compose_probe_line(response, is_current_stage, uni)
    full_summary = f"{summary_body}\n{probe_line}" if summary_body else probe_line

    updated = stage_reasoning.model_copy(update={REASONING_KEY: full_summary})
    return {"stage_reasoning": updated.model_dump()}


def route_after_planner(state: PathFinderState) -> str:
    packet = get_uni_research(state)
    if packet.need_research and packet.search_query:
        return "uni_researcher"
    return "uni_synthesizer"


builder = StateGraph(PathFinderState)
builder.add_node("confident", confident_node)
builder.add_node("reopen_invalidator", reopen_invalidator_node)
builder.add_node("uni_research_planner", uni_research_planner)
builder.add_node("uni_researcher", uni_researcher)
builder.add_node("uni_synthesizer", uni_synthesizer)
builder.add_edge(START, "confident")
builder.add_edge("confident", "reopen_invalidator")
builder.add_edge("reopen_invalidator", "uni_research_planner")
builder.add_conditional_edges(
    "uni_research_planner",
    route_after_planner,
    ["uni_researcher", "uni_synthesizer"],
)
builder.add_edge("uni_researcher", "uni_synthesizer")
builder.add_edge("uni_synthesizer", END)
uni_graph = builder.compile()
