import os

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict

from backend.data.contracts.research_sources import MAJOR_REALITY_DOMAINS
from backend.data.contracts.stages import (
    STAGE_TO_PROFILE_KEY,
    STAGE_TO_QUEUE_KEY,
    STAGE_TO_REASONING_KEY,
)
from backend.data.prompts.major import (
    MAJOR_CONFIDENT_PROMPT,
    MAJOR_RESEARCH_PLAN_PROMPT,
    MAJOR_SYNTHESIS_PROMPT,
)
from backend.data.state import MajorProfile, MajorResearch, PathFinderState, StageReasoning
from backend.retrieval import SearchRequest, format_search_response, search_web

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

STAGE = "major"
PROFILE_KEY = STAGE_TO_PROFILE_KEY[STAGE]
QUEUE_KEY = STAGE_TO_QUEUE_KEY[STAGE]
REASONING_KEY = STAGE_TO_REASONING_KEY[STAGE]


class ConfidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    major: MajorProfile


class MajorResearchPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    need_research: bool
    query_focus: str
    contradiction_to_test: str
    search_query: str
    domain_bucket: str


class MajorAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    major_summary: str
    probe_field: str
    probe_tension: str
    probe_instruction: str


planner_llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=300).with_structured_output(MajorResearchPlan)
analysis_llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=450).with_structured_output(MajorAnalysis)
confident_llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=450).with_structured_output(ConfidentOutput)


DOMAIN_BUCKETS: dict[str, tuple[str, ...]] = {
    "major_necessity": MAJOR_REALITY_DOMAINS,
    "major_curriculum": MAJOR_REALITY_DOMAINS,
    "major_transferability": MAJOR_REALITY_DOMAINS,
    "major_dreamer_barrier": MAJOR_REALITY_DOMAINS,
    "none": (),
}


def get_stage_reasoning(state: PathFinderState) -> StageReasoning:
    raw = state.get("stage_reasoning") or {}
    if isinstance(raw, dict):
        return StageReasoning(**raw)
    return raw


def get_major_research(state: PathFinderState) -> MajorResearch:
    raw = state.get("major_research")
    if raw is None:
        return MajorResearch()
    if isinstance(raw, dict):
        return MajorResearch(**raw)
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


def _infer_probe_field(major: object) -> str:
    if major is None:
        return "required_skills_coverage"

    ordered_fields = [
        "required_skills_coverage",
        "curriculum_style",
        "field",
    ]

    for field_name in ordered_fields:
        field = major.get(field_name) if isinstance(major, dict) else getattr(major, field_name, None)
        content, confidence = _extract_field_meta(field)
        if confidence < 0.7 or content in {"", "unclear", "not discussed", "not yet"}:
            return field_name

    return "required_skills_coverage"


def _default_probe_instruction(field_name: str) -> str:
    defaults = {
        "required_skills_coverage": "force the student to defend why this major is worth the years versus a portfolio or self-taught route.",
        "curriculum_style": "force a choice between the program's teaching reality and the student's actual learning mode.",
        "field": "force a trade-off between the named major and the strongest safer or more direct alternative.",
    }
    return defaults.get(field_name, "force a concrete trade-off instead of a vague preference.")


def _strip_legacy_probe_suffix(text: str) -> str:
    lines = [line for line in (text or "").strip().splitlines() if line.strip()]
    while lines and lines[-1].strip().upper().startswith("PROBE:"):
        lines.pop()
    return "\n".join(lines).strip()


def _compose_probe_line(response: MajorAnalysis, is_current_stage: bool, major: object) -> str:
    if not is_current_stage:
        return "PROBE: NONE (passive analysis only)"

    field_name = (response.probe_field or "").strip()
    if not field_name or field_name.upper() == "NONE":
        field_name = _infer_probe_field(major)

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


def _run_web_research(packet: MajorResearch) -> MajorResearch:
    bucket = (packet.domain_bucket or "none").strip().lower()
    allowed_domains = list(DOMAIN_BUCKETS.get(bucket, ()))
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
    major = state.get(PROFILE_KEY)

    response = confident_llm.invoke([SystemMessage(MAJOR_CONFIDENT_PROMPT.format(major=major or ""))] + messages)
    return {PROFILE_KEY: response.major.model_dump()}


def major_research_planner(state: PathFinderState) -> dict:
    messages = state[QUEUE_KEY]
    stage_reasoning = get_stage_reasoning(state)
    major = state.get(PROFILE_KEY)
    major_research = get_major_research(state)
    thinking = state.get("thinking", {})
    purpose = state.get("purpose", {})
    goals = state.get("goals", {})
    job = state.get("job", {})
    message_tag = state.get("message_tag", {})
    is_current_stage = get_current_stage(state) == STAGE

    response = planner_llm.invoke(
        [SystemMessage(MAJOR_RESEARCH_PLAN_PROMPT.format(
            is_current_stage=is_current_stage,
            stage_reasoning=getattr(stage_reasoning, REASONING_KEY),
            major=major or "",
            major_research=major_research.model_dump(),
            thinking=thinking or "",
            purpose=purpose or "",
            goals=goals or "",
            job=job or "",
            message_tag=message_tag or "",
        ))] + messages
    )

    packet = MajorResearch(
        need_research=response.need_research and bool((response.search_query or "").strip()),
        query_focus=(response.query_focus or "").strip(),
        contradiction_to_test=(response.contradiction_to_test or "").strip(),
        search_query=(response.search_query or "").strip(),
        domain_bucket=(response.domain_bucket or "none").strip().lower(),
        evidence_summary="",
        cited_sources=[],
        market_verdict="",
        research_complete=False,
    )

    return {"major_research": packet.model_dump()}


def major_researcher(state: PathFinderState) -> dict:
    packet = get_major_research(state)
    if not packet.need_research or not packet.search_query:
        return {"major_research": packet.model_copy(update={"research_complete": False}).model_dump()}

    researched = _run_web_research(packet)
    return {"major_research": researched.model_dump()}


def major_synthesizer(state: PathFinderState) -> dict:
    messages = state[QUEUE_KEY]
    stage_reasoning = get_stage_reasoning(state)
    major = state.get(PROFILE_KEY)
    major_research = get_major_research(state)
    thinking = state.get("thinking", {})
    purpose = state.get("purpose", {})
    goals = state.get("goals", {})
    job = state.get("job", {})
    message_tag = state.get("message_tag", {})
    is_current_stage = get_current_stage(state) == STAGE

    response = analysis_llm.invoke(
        [SystemMessage(MAJOR_SYNTHESIS_PROMPT.format(
            is_current_stage=str(is_current_stage),
            stage_reasoning=getattr(stage_reasoning, REASONING_KEY),
            major=major or "",
            major_research=major_research.model_dump(),
            thinking=thinking or "",
            purpose=purpose or "",
            goals=goals or "",
            job=job or "",
            message_tag=message_tag or "",
        ))] + messages
    )

    summary_body = _strip_legacy_probe_suffix(response.major_summary)
    probe_line = _compose_probe_line(response, is_current_stage, major)
    full_summary = f"{summary_body}\n{probe_line}" if summary_body else probe_line

    updated = stage_reasoning.model_copy(update={REASONING_KEY: full_summary})
    return {"stage_reasoning": updated.model_dump()}


def route_after_planner(state: PathFinderState) -> str:
    packet = get_major_research(state)
    if packet.need_research and packet.search_query:
        return "major_researcher"
    return "major_synthesizer"


builder = StateGraph(PathFinderState)
builder.add_node("confident", confident_node)
builder.add_node("major_research_planner", major_research_planner)
builder.add_node("major_researcher", major_researcher)
builder.add_node("major_synthesizer", major_synthesizer)
builder.add_edge(START, "confident")
builder.add_edge("confident", "major_research_planner")
builder.add_conditional_edges(
    "major_research_planner",
    route_after_planner,
    ["major_researcher", "major_synthesizer"],
)
builder.add_edge("major_researcher", "major_synthesizer")
builder.add_edge("major_synthesizer", END)
major_graph = builder.compile()
