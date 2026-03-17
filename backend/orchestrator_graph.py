from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, RemoveMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict
from backend.data.state import PathFinderState, StageCheck, MessageTag, UserTag
from backend.data.prompts.orchestrator import INPUT_PARSER_PROMPT, SUMMARIZER_PROMPT
from dotenv import load_dotenv
import os, tiktoken, json

#prep
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
memory = MemorySaver()
TOKEN_CAP = 4000
_enc = tiktoken.encoding_for_model("gpt-5")

#def output
class InputOutputStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage_check: StageCheck
    message_tag: MessageTag
    user_tag: UserTag
    active_tags: list[str]

#llm
llm = ChatOpenAI(model="gpt-5.2", temperature=0.5)
low_llm = ChatOpenAI(model="gpt-5-mini")
input_llm = llm.with_structured_output(InputOutputStyle)

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
    stage_check = state.get("stage_check") or {}
    profile_summary = state.get("profile_summary") or {}
    user_tag = state.get("user_tag") or {}
    troll_warnings = state.get("troll_warnings")
    response = input_llm.invoke(
        [SystemMessage(INPUT_PARSER_PROMPT.format(
            stage_check = stage_check,
            profile_summary = profile_summary,
            user_tag = user_tag,
            troll_warnings = troll_warnings
        ))] + state["messages"]
    )
    return {
        "stage_check": response.stage_check.model_dump(),
        "message_tag": response.message_tag.model_dump(),
        "user_tag":    response.user_tag.model_dump(),
        "active_tags": response.active_tags,
    }

#edge
def route(state: PathFinderState):
    return "summarizer" if state["limit_hit"] else "input_parser"

#graph
builder = StateGraph(PathFinderState)
builder.add_node("check", check_node)
builder.add_node("summarizer", summarizer_node)
builder.add_node("input_parser", input_parser)
builder.add_edge(START, "check")
builder.add_conditional_edges(
    "check",
    route,
    ["summarizer", "input_parser"]
)
builder.add_edge("summarizer", "input_parser")
builder.add_edge("input_parser", END)
input_orchestrator = builder.compile()