from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os
from backend.data.state import PathFinderState, GoalsProfile, StageReasoning
from backend.data.prompts.goals import GOALS_DRILL_PROMPT, CONFIDENT_PROMPT as GOALS_CONFIDENT_PROMPT
from backend.data.contracts.stages import (
    STAGE_TO_PROFILE_KEY,
    STAGE_TO_QUEUE_KEY,
    STAGE_TO_REASONING_KEY,
)

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# contract prep
STAGE = "goals"
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

# structured outputs
class GoalsAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goals_summary: str  # analysis → written to stage_reasoning.goals

class ConfidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goals: GoalsProfile

# llm
llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=450)
analysis_llm  = llm.with_structured_output(GoalsAnalysis)
confident_llm = llm.with_structured_output(ConfidentOutput)

# nodes
def goals_agent(state: PathFinderState) -> dict:
    messages        = state[QUEUE_KEY]
    stage_reasoning = get_stage_reasoning(state)
    goals           = state.get(PROFILE_KEY)
    purpose         = state.get("purpose")
    message_tag     = state.get("message_tag")

    is_current_stage = str(get_current_stage(state) == STAGE)

    response = analysis_llm.invoke(
        [SystemMessage(GOALS_DRILL_PROMPT.format(
            is_current_stage=is_current_stage,
            stage_reasoning=getattr(stage_reasoning, REASONING_KEY),
            goals=goals or "",
            purpose=purpose or "",
            message_tag=message_tag or "",
        ))] + messages
    )
    updated = stage_reasoning.model_copy(update={REASONING_KEY: response.goals_summary})
    return {"stage_reasoning": updated.model_dump()}

def confident_node(state: PathFinderState) -> dict:
    messages = state[QUEUE_KEY]
    goals    = state.get(PROFILE_KEY)

    response = confident_llm.invoke(
        [SystemMessage(GOALS_CONFIDENT_PROMPT.format(goals=goals or ""))] + messages
    )
    return {PROFILE_KEY: response.goals.model_dump()}

# graph
builder = StateGraph(PathFinderState)
builder.add_node("goals_agent", goals_agent)
builder.add_node("confident",   confident_node)
builder.add_edge(START, "confident")
builder.add_edge("confident",   "goals_agent")
builder.add_edge("goals_agent", END)
goals_graph = builder.compile()
