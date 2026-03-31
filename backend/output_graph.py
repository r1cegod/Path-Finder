from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import os
from backend.data.state import PathFinderState, MessageTag, UserTag, StageCheck
from backend.data.prompts.output import build_compiler_prompt

#prep
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
output_llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0.7)

#nodes
def context_compiler(state: PathFinderState) -> dict:
    return {"compiler_prompt": build_compiler_prompt(state)}

def output_compiler(state: PathFinderState) -> dict:
    compiler_prompt = state.get("compiler_prompt") or ""
    response = output_llm.invoke(
        [SystemMessage(content=compiler_prompt)] + state["messages"]
    )
    return {"messages": [AIMessage(content=response.content)]}


#GRAPH
builder = StateGraph(PathFinderState)
builder.add_node("context_compiler", context_compiler)
builder.add_node("output_compiler", output_compiler)
builder.add_edge(START, "context_compiler")
builder.add_edge("context_compiler", "output_compiler")
builder.add_edge("output_compiler", END)
output_graph = builder.compile()
