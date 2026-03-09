from xml.etree.ElementInclude import include
from langchain_core.messages import filter_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from backend.data.state import PathFinderState
from pydantic import BaseModel, ConfigDict
from backend.data.prompts.purpose import SUMMARY_PROMPT, PURPOSE_DRILL_PROMPT, CONFIDENT_PROMPT
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
memory=MemorySaver()

#classies
class PurposeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose_message: str
class SummaryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_summary: str
class PurposeDict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str
    confident_score: int
class ConfidentDict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    core_desire:       PurposeDict
    work_relationship: PurposeDict
    ai_stance:         PurposeDict
    location_vision:   PurposeDict
    risk_philosophy:   PurposeDict
    key_quote:         PurposeDict
class ConfidenOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose : ConfidentDict

#llm define
llm = ChatOpenAI(model="gpt-5-mini", temperature=0.5)
structured_llm = llm.with_structured_output(PurposeOutput)
summary_llm = llm.with_structured_output(SummaryOutput)
confident_llm = llm.with_structured_output(ConfidenOutput)

#NODES
def purpose_agent(state: PathFinderState) -> dict:
    human_message = filter_messages(
        state["purpose_message"],
        include_types=["human"]
    )
    profile_summary = state.get("profile_summary", "")
    purpose = state["purpose"]
    response = structured_llm.invoke(
        [SystemMessage(PURPOSE_DRILL_PROMPT.format(profile_summary=profile_summary, purpose=purpose))]+ human_message)
    return {"purpose_message": response.purpose_message}
def summary_node(state: PathFinderState):
    profile_summary = state.get("profile_summary", "")
    response = summary_llm.invoke([SystemMessage(SUMMARY_PROMPT.format(profile_summary=profile_summary))] + state["purpose_message"])
    return {"profile_summary": response.profile_summary}
def confident_node(state: PathFinderState):
    messages = state["purpose_message"]
    purpose = state["purpose"]
    response = confident_llm.invoke(
        [SystemMessage(CONFIDENT_PROMPT.format(purpose=purpose))]+ messages
    )
    return {"purpose": response.purpose}

#graph
builder = StateGraph(PathFinderState)
builder.add_node("purpose_agent", purpose_agent)
builder.add_node("summary", summary_node)
builder.add_node("confident", confident_node)
builder.add_edge(START, "confident")
builder.add_edge("confident", "summary")
builder.add_edge("summary", "purpose_agent")
builder.add_edge("purpose_agent", END)
purpose_graph = builder.compile()