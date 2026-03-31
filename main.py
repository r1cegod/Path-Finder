from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.orchestrator_graph import input_orchestrator
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
async def health():
    return {"status": "ok"}

class ChatRequest(BaseModel):
    message: str

class TestRequest(BaseModel):
    brain_type:  list[str] = []
    riasec_top:  list[str] = []


def serialize_state(result: dict) -> dict:
    """Map PathFinderState → frontend appState shape."""
    stage = result.get("stage") or {}
    current_stage = stage.get("current_stage", "thinking") if isinstance(stage, dict) else "thinking"

    completed = []
    for key in ["thinking", "purpose", "goals", "job", "major"]:
        profile = result.get(key)
        if isinstance(profile, dict) and profile.get("done"):
            completed.append(key)

    return {
        "currentStage":    current_stage,
        "completedStages": completed,
        "turn_count":      result.get("turn_count", 0),
        "thinking":        result.get("thinking"),
        "purpose":         result.get("purpose"),
        "goals":           result.get("goals"),
        "job":             result.get("job"),
        "major":           result.get("major"),
        "uni":             result.get("university"),
        "user_tag":        result.get("user_tag"),
    }


@app.post("/test/{session_id}")
async def test_submit(session_id: str, request: TestRequest):  # noqa: ARG001
    async def generate():
        # Direct state write — no LLM. Frontend merges into appState.thinking.
        thinking_patch = {
            **({"brain_type": request.brain_type} if request.brain_type else {}),
            **({"riasec_top": request.riasec_top} if request.riasec_top else {}),
        }
        yield f"data: {json.dumps({'type': 'state', 'data': {'thinking': thinking_patch}})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/chat/{session_id}")
async def chat_stream(session_id: str, request: ChatRequest):
    state  = {"messages": [{"role": "user", "content": request.message}]}
    config = {"configurable": {"thread_id": session_id}}

    async def generate():
        try:
            async for event in input_orchestrator.astream_events(state, config=config, version="v2"):
                kind     = event["event"]
                metadata = event.get("metadata", {})
                node     = metadata.get("langgraph_node", "")

                if kind == "on_chat_model_stream" and node == "output_compiler":
                    # Only stream tokens from the human-facing response node
                    token = event["data"]["chunk"].content
                    if token:
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

                elif kind == "on_chain_end" and event.get("name") == "LangGraph" and not node:
                    # Only capture state from top-level graph (subgraphs have node set)
                    result = event["data"].get("output", {})
                    yield f"data: {json.dumps({'type': 'state', 'data': serialize_state(result)})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
