from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os
from backend.data.state import PathFinderState, GoalsProfile, GoalsLongProfile, GoalsShortProfile, StageReasoning
from backend.data.prompts.goals import GOALS_DRILL_PROMPT, CONFIDENT_PROMPT as GOALS_CONFIDENT_PROMPT

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
memory = MemorySaver()

# dict to object
def get_stage_reasoning(state: PathFinderState) -> StageReasoning:
    raw = state.get("stage_reasoning") or {}
    if isinstance(raw, dict):
        return StageReasoning(**raw)
    return raw

# structured outputs
class GoalsAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goals_summary: str  # analysis → written to stage_reasoning.goals

class ConfidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goals: GoalsProfile

# llm
llm = ChatOpenAI(model="gpt-5.4-mini")
analysis_llm  = llm.with_structured_output(GoalsAnalysis)
confident_llm = llm.with_structured_output(ConfidentOutput)

# nodes
def goals_agent(state: PathFinderState) -> dict:
    messages        = state["goals_message"]
    stage_reasoning = get_stage_reasoning(state)
    goals           = state.get("goals")

    response = analysis_llm.invoke(
        [SystemMessage(GOALS_DRILL_PROMPT.format(
            stage_reasoning=stage_reasoning.goals,
            goals=goals or "",
        ))] + messages
    )
    updated = stage_reasoning.model_copy(update={"goals": response.goals_summary})
    return {"stage_reasoning": updated.model_dump()}

def confident_node(state: PathFinderState) -> dict:
    messages = state["goals_message"]
    goals    = state.get("goals")

    response = confident_llm.invoke(
        [SystemMessage(GOALS_CONFIDENT_PROMPT.format(goals=goals or ""))] + messages
    )
    return {"goals": response.goals.model_dump()}

# graph
builder = StateGraph(PathFinderState)
builder.add_node("goals_agent", goals_agent)
builder.add_node("confident",   confident_node)
builder.add_edge(START, "confident")
builder.add_edge("confident",   "goals_agent")
builder.add_edge("goals_agent", END)
goals_graph = builder.compile()
