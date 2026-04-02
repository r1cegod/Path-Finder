from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os
from backend.data.state import PathFinderState, UniProfile, StageReasoning
from backend.data.prompts.uni import UNI_DRILL_PROMPT, UNI_CONFIDENT_PROMPT
from backend.data.contracts.stages import (
    STAGE_TO_PROFILE_KEY,
    STAGE_TO_QUEUE_KEY,
    STAGE_TO_REASONING_KEY,
)
from backend.tools import search

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# contract prep
STAGE = "university"
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
    university: UniProfile

# llm — uni_agent uses bind_tools for data retrieval
tools = [search]
llm = ChatOpenAI(model="gpt-5.4-mini")
agent_llm     = llm.bind_tools(tools)
confident_llm = llm.with_structured_output(ConfidentOutput)

tool_node = ToolNode(tools=tools, messages_key=QUEUE_KEY)

# nodes
def uni_agent(state: PathFinderState) -> dict:
    messages        = state[QUEUE_KEY]
    stage_reasoning = get_stage_reasoning(state)
    uni             = state.get(PROFILE_KEY)
    
    # The Prompt expects these kwargs in .format()
    thinking    = state.get("thinking", {})
    purpose     = state.get("purpose", {})
    goals       = state.get("goals", {})
    job         = state.get("job", {})
    major       = state.get("major", {})
    message_tag = state.get("message_tag", {})
    summary     = state.get("summary", "")
    is_current_stage = get_current_stage(state) == STAGE

    response = agent_llm.invoke(
        [SystemMessage(UNI_DRILL_PROMPT.format(
            is_current_stage=is_current_stage,
            stage_reasoning=getattr(stage_reasoning, REASONING_KEY),
            uni=uni or "",
            thinking=thinking or "",
            purpose=purpose or "",
            goals=goals or "",
            job=job or "",
            major=major or "",
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
    uni    = state.get(PROFILE_KEY)

    response = confident_llm.invoke(
        [SystemMessage(UNI_CONFIDENT_PROMPT.format(uni=uni or ""))] + messages
    )
    return {PROFILE_KEY: response.university.model_dump()}

# graph
builder = StateGraph(PathFinderState)
builder.add_node("uni_agent", uni_agent)
builder.add_node("confident", confident_node)
builder.add_node("tools",     tool_node)
builder.add_edge(START, "confident")
builder.add_edge("confident", "uni_agent")
builder.add_conditional_edges(
    "uni_agent",
    lambda state: tools_condition(state, messages_key=QUEUE_KEY),
    ["tools", END]
)
builder.add_edge("tools", "uni_agent")
uni_graph = builder.compile()
