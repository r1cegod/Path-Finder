from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os
from backend.data.state import PathFinderState, ThinkingProfile, StageReasoning
from backend.data.prompts.thinking import THINKING_DRILL_PROMPT, CONFIDENT_PROMPT

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
memory = MemorySaver()

# dict to object
def get_stage_reasoning(state: PathFinderState) -> StageReasoning:
    raw = state.get("stage_reasoning") or {}
    if isinstance(raw, dict):
        return StageReasoning(**raw)
    return raw

def get_thinking_profile(state: PathFinderState) -> ThinkingProfile | None:
    raw = state.get("thinking")
    if isinstance(raw, dict):
        return ThinkingProfile(**raw)
    return raw

# structured outputs
class ThinkingAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thinking_summary: str  # analysis → written to stage_reasoning.thinking

class ConfidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thinking: ThinkingProfile

# llm
llm          = ChatOpenAI(model="gpt-5.4-mini")
analysis_llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=450).with_structured_output(ThinkingAnalysis)
confident_llm = llm.with_structured_output(ConfidentOutput)

# nodes
def thinking_agent(state: PathFinderState) -> dict:
    messages        = state["thinking_style_message"]
    stage_reasoning = get_stage_reasoning(state)
    thinking        = get_thinking_profile(state)

    stage_raw = state.get("stage") or {}
    current_stage = stage_raw.get("current_stage", "thinking") if isinstance(stage_raw, dict) else getattr(stage_raw, "current_stage", "thinking")
    is_current_stage = str(current_stage == "thinking")

    response = analysis_llm.invoke(
        [SystemMessage(THINKING_DRILL_PROMPT.format(
            is_current_stage=is_current_stage,
            stage_reasoning=stage_reasoning.thinking,
            thinking=thinking or "",
        ))] + messages
    )
    updated = stage_reasoning.model_copy(update={"thinking": response.thinking_summary})
    return {"stage_reasoning": updated.model_dump()}

def confident_node(state: PathFinderState) -> dict:
    messages = state["thinking_style_message"]
    thinking = get_thinking_profile(state)

    response = confident_llm.invoke(
        [SystemMessage(CONFIDENT_PROMPT.format(
            thinking=thinking or ""
        ))] + messages
    )
    return {"thinking": response.thinking.model_dump()}

# graph
builder = StateGraph(PathFinderState)
builder.add_node("thinking_agent", thinking_agent)
builder.add_node("confident", confident_node)
builder.add_edge(START, "confident")
builder.add_edge("confident", "thinking_agent")
builder.add_edge("thinking_agent", END)
thinking_graph = builder.compile()