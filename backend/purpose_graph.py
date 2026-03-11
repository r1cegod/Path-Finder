from langchain_core.messages import filter_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os
from backend.data.state import PathFinderState, PurposeProfile, ProfileSummary
from backend.data.prompts.purpose import SUMMARY_PROMPT, PURPOSE_DRILL_PROMPT, CONFIDENT_PROMPT

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
memory = MemorySaver()

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
llm = ChatOpenAI(model="gpt-5-mini", temperature=0.5)
structured_llm = llm.with_structured_output(PurposeOutput)
summary_llm = llm.with_structured_output(SummaryOutput)
confident_llm = llm.with_structured_output(ConfidenOutput)

#node
def purpose_agent(state: PathFinderState) -> dict:
    human_message = filter_messages(
        state["purpose_message"],
        include_types=["human"]
    )
    profile_summary = get_profile_summary(state)
    purpose = state.get("purpose")
    response = structured_llm.invoke(
        [SystemMessage(PURPOSE_DRILL_PROMPT.format(
            profile_summary=profile_summary.purpose,
            purpose=purpose
        ))] + human_message
    )
    return {"purpose_message": response.purpose_message}

def summary_node(state: PathFinderState) -> dict:
    profile_summary = get_profile_summary(state)
    purpose = state.get("purpose")
    response = summary_llm.invoke(
        [SystemMessage(SUMMARY_PROMPT.format(
            profile_summary=profile_summary.purpose,
            purpose=purpose
        ))]
        + state["purpose_message"]
        )
    updated = profile_summary.model_copy(update={"purpose": response.purpose})
    return {"profile_summary": updated.model_dump()}

def confident_node(state: PathFinderState) -> dict:
    messages = state["purpose_message"]
    purpose = state.get("purpose")
    response = confident_llm.invoke(
        [SystemMessage(CONFIDENT_PROMPT.format(purpose=purpose))] + messages)
    return {"purpose": response.purpose.model_dump()}

#graph
builder = StateGraph(PathFinderState)
builder.add_node("purpose_agent",purpose_agent)
builder.add_node("summary",summary_node)
builder.add_node("confident",confident_node)
builder.add_edge(START,"confident")
builder.add_edge("confident","summary")
builder.add_edge("summary","purpose_agent")
builder.add_edge("purpose_agent", END)

purpose_graph = builder.compile()