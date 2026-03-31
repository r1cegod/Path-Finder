from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os
from backend.data.state import PathFinderState, MajorProfile, StageReasoning
from backend.data.prompts.major import MAJOR_DRILL_PROMPT, MAJOR_CONFIDENT_PROMPT
from backend.tools import search

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
class ConfidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    major: MajorProfile

# llm — major_agent uses bind_tools for data retrieval
tools = [search]
llm = ChatOpenAI(model="gpt-5.4-mini")
agent_llm     = llm.bind_tools(tools)
confident_llm = llm.with_structured_output(ConfidentOutput)

tool_node = ToolNode(tools=tools, messages_key="major_message")

# nodes
def major_agent(state: PathFinderState) -> dict:
    messages        = state["major_message"]
    stage_reasoning = get_stage_reasoning(state)
    major           = state.get("major")
    
    # The Prompt expects these kwargs in .format()
    thinking    = state.get("thinking", {})
    purpose     = state.get("purpose", {})
    goals       = state.get("goals", {})
    job         = state.get("job", {})
    message_tag = state.get("message_tag", {})
    summary     = state.get("summary", "")
    is_current_stage = (state.get("stage", {}).get("current_stage") == "major")

    response = agent_llm.invoke(
        [SystemMessage(MAJOR_DRILL_PROMPT.format(
            is_current_stage=is_current_stage,
            stage_reasoning=stage_reasoning.major,
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
        return {"major_message": response} # tools_condition needs this to route
        
    # Branch 2: LLM wrote the final PROBE reasoning
    updated = stage_reasoning.model_copy(update={"major": response.content})
    return {"stage_reasoning": updated.model_dump(), "major_message": response}

def confident_node(state: PathFinderState) -> dict:
    messages = state["major_message"]
    major    = state.get("major")

    response = confident_llm.invoke(
        [SystemMessage(MAJOR_CONFIDENT_PROMPT.format(major=major or ""))] + messages
    )
    return {"major": response.major.model_dump()}

# graph
builder = StateGraph(PathFinderState)
builder.add_node("major_agent", major_agent)
builder.add_node("confident",   confident_node)
builder.add_node("tools",       tool_node)
builder.add_edge(START, "confident")
builder.add_edge("confident",   "major_agent")
builder.add_conditional_edges(
    "major_agent",
    lambda state: tools_condition(state, messages_key="major_message"),
    ["tools", END]
)
builder.add_edge("tools", "major_agent")
major_graph = builder.compile()
