from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import os
import re
import unicodedata
from backend.data.state import PathFinderState, StageCheck
from backend.data.prompts.output import build_compiler_prompt
from backend.data.contracts.stages import is_stage_name, STAGE_TO_QUEUE_KEY

#prep
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# Keep the final student-facing compiler deterministic so Stage 4 preserves the
# analyst's exact PROBE tension instead of drifting into softer phrasing.
output_llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0.0)


def _sanitize_student_reply(text: str) -> str:
    def keep_char(ch: str) -> bool:
        if ch in "\n\r\t":
            return True
        category = unicodedata.category(ch)
        if category[0] in {"Z", "P", "N"}:
            return True
        if category.startswith("L"):
            return "LATIN" in unicodedata.name(ch, "")
        return False

    cleaned = "".join(ch if keep_char(ch) else " " for ch in text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()

#dict to obj
def get_stage(state: PathFinderState) -> StageCheck:
    raw = state.get("stage") or {}
    if isinstance(raw, dict):
        return StageCheck(**raw)
    return raw

#nodes
def context_compiler(state: PathFinderState) -> dict:
    return {"compiler_prompt": build_compiler_prompt(state)}

def output_compiler(state: PathFinderState) -> dict:
    compiler_prompt = state.get("compiler_prompt") or ""
    response = output_llm.invoke(
        [SystemMessage(content=compiler_prompt)] + state["messages"]
    )
    content = response.content if isinstance(response.content, str) else str(response.content)
    ai_message = AIMessage(content=_sanitize_student_reply(content))
    updates = {"messages": [ai_message]}

    stage = get_stage(state)
    context_stages = list(dict.fromkeys(list(stage.stage_related or [])))
    if context_stages:
        for s in context_stages:
            if is_stage_name(s):
                updates[STAGE_TO_QUEUE_KEY[s]] = [ai_message]
                
    return updates

#GRAPH
builder = StateGraph(PathFinderState)
builder.add_node("context_compiler", context_compiler)
builder.add_node("output_compiler", output_compiler)
builder.add_edge(START, "context_compiler")
builder.add_edge("context_compiler", "output_compiler")
builder.add_edge("output_compiler", END)
output_graph = builder.compile()
