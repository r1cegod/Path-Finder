from langchain_core.messages import filter_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, RemoveMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os, tiktoken
from backend.data.state import PathFinderState, PurposeProfile, ProfileSummary
from backend.data.prompts.purpose import SUMMARY_PROMPT, PURPOSE_DRILL_PROMPT, CONFIDENT_PROMPT

#prep
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
memory = MemorySaver()
TOKEN_CAP = 1000
_enc = tiktoken.encoding_for_model("gpt-5-mini")

#dict to object
def get_profile_summary(state: PathFinderState) -> ProfileSummary:
    raw = state.get("profile_summary") or {}
    if isinstance(raw, dict):
        return ProfileSummary(**raw)
    return raw

#classies
class PurposeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose_message: str
class SummaryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose: str
class ConfidenOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose: PurposeProfile

#llm
llm = ChatOpenAI(model="gpt-5.4-mini")
structured_llm = llm.with_structured_output(PurposeOutput)
summary_llm = llm.with_structured_output(SummaryOutput)
confident_llm = llm.with_structured_output(ConfidenOutput)

#node
def check_node(state: PathFinderState) -> dict:
    total = 3
    for msg in state["purpose_message"]:
        total += 3 + len(_enc.encode(msg.content))
    return {
        "purpose_limit": total >= TOKEN_CAP, 
        "input_token": total
    }

def summarizer_node(state: PathFinderState) -> dict:
    profile_summary = get_profile_summary(state)
    purpose = state.get("purpose")
    messages  = state["purpose_message"]
    cutoff    = len(messages) * 3 // 4
    to_compress = messages[:cutoff]
    response = summary_llm.invoke(
        [SystemMessage(SUMMARY_PROMPT.format(
            profile_summary=profile_summary.purpose,
            purpose=purpose or ""
        ))]
        + to_compress
    )
    removals = [RemoveMessage(id=m.id) for m in to_compress]
    updated = profile_summary.model_copy(update={"purpose": response.purpose})
    return {
        "purpose_message": removals,
        "profile_summary": updated.model_dump(),
        "purpose_limit": False,
    }

def purpose_agent(state: PathFinderState) -> dict:
    messages = state["purpose_message"]
    profile_summary = get_profile_summary(state)
    purpose = state.get("purpose")
    response = structured_llm.invoke(
        [SystemMessage(PURPOSE_DRILL_PROMPT.format(
            profile_summary=profile_summary.purpose,
            purpose=purpose or ""
        ))] + messages
    )
    return {"purpose_message": response.purpose_message}

def confident_node(state: PathFinderState) -> dict:
    messages = state["purpose_message"]
    purpose = state.get("purpose")
    response = confident_llm.invoke(
        [SystemMessage(CONFIDENT_PROMPT.format(purpose=purpose or ""))] + messages)
    return {"purpose": response.purpose.model_dump()}

#edge
def check_sum(state: PathFinderState):
    return "summarizer" if state["purpose_limit"] else "confident"

#graph
builder = StateGraph(PathFinderState)
builder.add_node("purpose_agent",purpose_agent)
builder.add_node("confident",confident_node)
builder.add_node("check", check_node)
builder.add_node("summarizer", summarizer_node)
builder.add_edge(START,"check")
builder.add_conditional_edges(
    "check",
    check_sum,
    ["summarizer", "confident"]
)
builder.add_edge("summarizer","confident")
builder.add_edge("confident", "purpose_agent")
builder.add_edge("purpose_agent", END)
purpose_graph = builder.compile()