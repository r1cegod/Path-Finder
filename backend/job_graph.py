from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os
from backend.data.state import PathFinderState, JobProfile, StageReasoning
from backend.data.prompts.job import JOB_DRILL_PROMPT, JOB_CONFIDENT_PROMPT
from backend.data.contracts.stages import (
    STAGE_TO_PROFILE_KEY,
    STAGE_TO_QUEUE_KEY,
    STAGE_TO_REASONING_KEY,
)
from backend.tools import search

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# contract prep
STAGE = "job"
PROFILE_KEY = STAGE_TO_PROFILE_KEY[STAGE]
QUEUE_KEY = STAGE_TO_QUEUE_KEY[STAGE]
REASONING_KEY = STAGE_TO_REASONING_KEY[STAGE]

#dict to object
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

#classies
class ConfidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job: JobProfile

#llm
tools = [search]
llm = ChatOpenAI(model="gpt-5.4-mini")
agent_llm     = llm.bind_tools(tools)
confident_llm = llm.with_structured_output(ConfidentOutput)

tool_node = ToolNode(tools=tools, messages_key=QUEUE_KEY)

#nodes
def job_agent(state: PathFinderState) -> dict:
    messages        = state[QUEUE_KEY]
    stage_reasoning = get_stage_reasoning(state)
    job             = state.get(PROFILE_KEY)
    thinking        = state.get("thinking", {})
    purpose         = state.get("purpose", {})
    goals           = state.get("goals", {})
    message_tag     = state.get("message_tag", {})
    is_current_stage = get_current_stage(state) == STAGE

    response = agent_llm.invoke(
        [SystemMessage(JOB_DRILL_PROMPT.format(
            is_current_stage=is_current_stage,
            stage_reasoning=getattr(stage_reasoning, REASONING_KEY),
            job=job or "",
            thinking=thinking or "",
            purpose=purpose or "",
            goals=goals or "",
            message_tag=message_tag or "",
        ))] + messages
    )

    if hasattr(response, "tool_calls") and response.tool_calls:
        return {QUEUE_KEY: response}
        
    updated = stage_reasoning.model_copy(update={REASONING_KEY: response.content})
    return {"stage_reasoning": updated.model_dump()}

def confident_node(state: PathFinderState) -> dict:
    messages = state[QUEUE_KEY]
    job      = state.get(PROFILE_KEY)

    response = confident_llm.invoke(
        [SystemMessage(JOB_CONFIDENT_PROMPT.format(job=job or ""))] + messages
    )
    return {PROFILE_KEY: response.job.model_dump()}

# graph
builder = StateGraph(PathFinderState)
builder.add_node("job_agent",   job_agent)
builder.add_node("confident",   confident_node)
builder.add_node("tools",       tool_node)
builder.add_edge(START, "confident")
builder.add_edge("confident",   "job_agent")
builder.add_conditional_edges(
    "job_agent",
    lambda state: tools_condition(state, messages_key=QUEUE_KEY),
    ["tools", END]
)
builder.add_edge("tools", "job_agent")
job_graph = builder.compile()
