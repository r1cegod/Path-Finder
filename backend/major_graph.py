from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os
from backend.data.state import PathFinderState, MajorProfile, StageReasoning
from backend.data.prompts.major import MAJOR_DRILL_PROMPT, MAJOR_CONFIDENT_PROMPT
from backend.data.contracts.stages import (
    STAGE_TO_PROFILE_KEY,
    STAGE_TO_QUEUE_KEY,
    STAGE_TO_REASONING_KEY,
)
from backend.tools import search

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# contract prep
STAGE = "major"
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
class ConfidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    major: MajorProfile

# llm
tools = [search]
llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=450)
agent_llm     = llm.bind_tools(tools)
confident_llm = llm.with_structured_output(ConfidentOutput)

tool_node = ToolNode(tools=tools, messages_key=QUEUE_KEY)

# nodes
def major_agent(state: PathFinderState) -> dict:
    messages        = state[QUEUE_KEY]
    stage_reasoning = get_stage_reasoning(state)
    major           = state.get(PROFILE_KEY)
    
    # The Prompt expects these kwargs in .format()
    thinking    = state.get("thinking", {})
    purpose     = state.get("purpose", {})
    goals       = state.get("goals", {})
    job         = state.get("job", {})
    message_tag = state.get("message_tag", {})
    summary     = state.get("summary", "")
    is_current_stage = get_current_stage(state) == STAGE

    response = agent_llm.invoke(
        [SystemMessage(MAJOR_DRILL_PROMPT.format(
            is_current_stage=is_current_stage,
            stage_reasoning=getattr(stage_reasoning, REASONING_KEY),
            major=major or "",
            thinking=thinking or "",
            purpose=purpose or "",
            goals=goals or "",
            job=job or "",
            message_tag=message_tag or "",
            summary=summary,
        ))] + messages
    )
    
    # Branch 1: LLM issued a Search Query
    if hasattr(response, "tool_calls") and response.tool_calls:
        return {QUEUE_KEY: response} # tools_condition needs this to route
        
    # Branch 2: LLM wrote the final PROBE reasoning
    updated = stage_reasoning.model_copy(update={REASONING_KEY: response.content})
    return {"stage_reasoning": updated.model_dump()}

def confident_node(state: PathFinderState) -> dict:
    messages = state[QUEUE_KEY]
    major    = state.get(PROFILE_KEY)

    response = confident_llm.invoke(
        [SystemMessage(MAJOR_CONFIDENT_PROMPT.format(major=major or ""))] + messages
    )
    return {PROFILE_KEY: response.major.model_dump()}

# graph
builder = StateGraph(PathFinderState)
builder.add_node("major_agent", major_agent)
builder.add_node("confident",   confident_node)
builder.add_node("tools",       tool_node)
builder.add_edge(START, "confident")
builder.add_edge("confident",   "major_agent")
builder.add_conditional_edges(
    "major_agent",
    lambda state: tools_condition(state, messages_key=QUEUE_KEY),
    ["tools", END]
)
builder.add_edge("tools", "major_agent")
major_graph = builder.compile()
