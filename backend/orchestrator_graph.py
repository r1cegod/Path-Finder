from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, RemoveMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict
from backend.data.state import PathFinderState, StageCheck, MessageTag, UserTag
from backend.data.prompts.orchestrator import INPUT_PARSER_PROMPT, SUMMARIZER_PROMPT
from dotenv import load_dotenv
import os, tiktoken

STAGE_ORDER = ["thinking", "purpose", "goals", "job", "major", "university", "path"]
STAGE_INDEX = {name: i for i, name in enumerate(STAGE_ORDER)}

#prep
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
memory = MemorySaver()
TOKEN_CAP = 500
_enc = tiktoken.encoding_for_model("gpt-5")

#def output
class InputOutputStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deflection_reasoning: str
    tension_reasoning: str
    stage_related: list[str]
    forced_stage: str
    message_tag: MessageTag
    user_tag: UserTag
    rebound: bool

#llm
llm = ChatOpenAI(model="gpt-5.4", temperature=0.5)
low_llm = ChatOpenAI(model="gpt-5.4-mini")
input_llm = llm.with_structured_output(InputOutputStyle)

#dict to object
def get_stage(state: PathFinderState) -> StageCheck:
    raw = state.get("stage") or {}
    if isinstance(raw, dict):
        return StageCheck(**raw)
    return raw

#nodes
def check_node(state: PathFinderState) -> dict:
    total = 3
    for msg in state["messages"]:
        total += 3 + len(_enc.encode(msg.content))
    return {"limit_hit": total >= TOKEN_CAP}

def summarizer_node(state: PathFinderState) -> dict:
    messages = state["messages"]
    cutoff = len(messages) * 3 // 4
    to_compress = messages[:cutoff]
    summary = state["summary"]
    user_tag = state.get("user_tag") or {}
    response = low_llm.invoke(
        [SystemMessage(content=SUMMARIZER_PROMPT.format(
            summary = summary,
            user_tag = user_tag
        ))] + to_compress
    )
    removals = [RemoveMessage(id=m.id) for m in to_compress]
    return {
        "messages":  removals,
        "summary":   response.content,
        "limit_hit": False,
    }

def input_parser(state: PathFinderState):
    stage_got = get_stage(state)
    profile_summary = state.get("profile_summary") or {}
    user_tag = state.get("user_tag") or {}
    troll_warnings = state.get("troll_warnings") or 0
    response = input_llm.invoke(
        [SystemMessage(INPUT_PARSER_PROMPT.format(
            profile_summary = profile_summary,
            user_tag = user_tag,
            current_stage = stage_got.current_stage,
            rebound = stage_got.rebound,
            troll_warnings = troll_warnings
        ))] + state["messages"]
    )
    stage = stage_got.model_copy(update={
        "stage_related": response.stage_related,
        "forced_stage": response.forced_stage,
        "rebound": response.rebound
    })
    return {
        "tension_reasoning": response.tension_reasoning,
        "deflection_reasoning": response.deflection_reasoning,
        "stage": stage.model_dump(),
        "message_tag": response.message_tag.model_dump(),
        "user_tag":    response.user_tag.model_dump(),
    }

def _is_done(profile) -> bool:
    if profile is None:
        return False
    if isinstance(profile, dict):
        return profile.get("done", False)
    return getattr(profile, "done", False)

def stage_manager(state: PathFinderState) -> dict:
    stage = get_stage(state)

    if stage.forced_stage:
        current = stage.forced_stage
    elif stage.current_stage:
        current = stage.current_stage
    else:
        current = "thinking"
    current_idx = STAGE_INDEX.get(current, 0)

    if stage.forced_stage and _is_done(state.get(stage.forced_stage)):
        current = STAGE_ORDER[min(current_idx + 1, 6)]
        current_idx = STAGE_INDEX.get(current, 0)
        stage = stage.model_copy(update={"forced_stage": "", "rebound": True})

    related = stage.stage_related
    future = [s for s in related if STAGE_INDEX.get(s, current_idx) > current_idx]
    past   = [s for s in related if STAGE_INDEX.get(s, current_idx) < current_idx]
    has_rebound    = bool(future) and stage.rebound  # both must agree: index + semantic gate
    has_contradict = bool(past)

    if has_rebound and has_contradict:
        updated = stage.model_copy(update={
            "current_stage": current, "rebound": True,
            "contradict": True, "contradict_target": past,
        })
    elif has_rebound:
        updated = stage.model_copy(update={
            "current_stage": current, "rebound": True,
            "contradict": False, "contradict_target": [],
        })
    elif has_contradict:
        updated = stage.model_copy(update={
            "current_stage": current, "rebound": False,
            "contradict": True, "contradict_target": past,
        })
    else:
        updated = stage.model_copy(update={
            "current_stage": current, "rebound": False,
            "contradict": False, "contradict_target": [],
        })

    return {"stage": updated.model_dump()}

#edge
def route(state: PathFinderState):
    return "summarizer" if state["limit_hit"] else "input_parser"

#graph
builder = StateGraph(PathFinderState)
builder.add_node("check", check_node)
builder.add_node("summarizer", summarizer_node)
builder.add_node("input_parser", input_parser)
builder.add_node("stage_manager", stage_manager)
builder.add_edge(START, "check")
builder.add_conditional_edges(
    "check",
    route,
    ["summarizer", "input_parser"]
)
builder.add_edge("summarizer", "input_parser")
builder.add_edge("input_parser", "stage_manager")
builder.add_edge("stage_manager", END)
input_orchestrator = builder.compile()