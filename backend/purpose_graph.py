from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import os
from backend.data.state import PathFinderState, PurposeProfile, StageReasoning
from backend.data.prompts.purpose import PURPOSE_DRILL_PROMPT, CONFIDENT_PROMPT

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
class PurposeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose_summary: str  # analysis → written to stage_reasoning.purpose

class ConfidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose: PurposeProfile

# llm
llm          = ChatOpenAI(model="gpt-5.4-mini")
analysis_llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=450).with_structured_output(PurposeAnalysis)
confident_llm = llm.with_structured_output(ConfidentOutput)

# nodes
def purpose_agent(state: PathFinderState) -> dict:
    messages        = state["purpose_message"]
    stage_reasoning = get_stage_reasoning(state)
    purpose         = state.get("purpose")

    thinking    = state.get("thinking")
    message_tag = state.get("message_tag")

    stage_raw = state.get("stage") or {}
    current_stage = stage_raw.get("current_stage", "thinking") if isinstance(stage_raw, dict) else getattr(stage_raw, "current_stage", "thinking")
    is_current_stage = str(current_stage == "purpose")

    response = analysis_llm.invoke(
        [SystemMessage(PURPOSE_DRILL_PROMPT.format(
            is_current_stage=is_current_stage,
            stage_reasoning=stage_reasoning.purpose,
            purpose=purpose or "",
            thinking=thinking or "",
            message_tag=message_tag or "",
        ))] + messages
    )
    updated = stage_reasoning.model_copy(update={"purpose": response.purpose_summary})
    return {"stage_reasoning": updated.model_dump()}

def confident_node(state: PathFinderState) -> dict:
    messages = state["purpose_message"]
    purpose  = state.get("purpose")

    response = confident_llm.invoke(
        [SystemMessage(CONFIDENT_PROMPT.format(purpose=purpose or ""))] + messages
    )
    return {"purpose": response.purpose.model_dump()}

# graph
builder = StateGraph(PathFinderState)
builder.add_node("purpose_agent", purpose_agent)
builder.add_node("confident", confident_node)
builder.add_edge(START, "confident")
builder.add_edge("confident", "purpose_agent")
builder.add_edge("purpose_agent", END)
purpose_graph = builder.compile()
