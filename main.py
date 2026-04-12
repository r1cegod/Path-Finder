from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel
from backend.debug_trace import (
    LiveTraceCollector,
    is_trace_active,
    serialize_value,
    start_trace_session,
    stop_trace_session,
)
from backend.orchestrator_graph import input_orchestrator
from backend.text_safety import sanitize_student_stream_token
from dotenv import load_dotenv
import json
import os

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://path-finder-rosy.vercel.app"],
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


class DebugStatePatchRequest(BaseModel):
    patch: dict


QUEUE_KEYS = {
    "messages",
    "thinking_style_message",
    "purpose_message",
    "goals_message",
    "job_message",
    "major_message",
    "uni_message",
    "routing_memory",
}

CHECKPOINT_PATCH_NODE = "__start__"


def _blank_thinking_profile() -> dict:
    def empty_field() -> dict:
        return {"content": "not yet", "confidence": 0.0}

    return {
        "done": False,
        "learning_mode": empty_field(),
        "env_constraint": empty_field(),
        "social_battery": empty_field(),
        "personality_type": empty_field(),
        "brain_type": [],
        "riasec_top": [],
        "riasec_scores": [],
    }


def _coerce_thinking_seed(current_thinking: object, thinking_patch: dict) -> dict:
    if hasattr(current_thinking, "model_dump"):
        current_thinking = current_thinking.model_dump()
    if not isinstance(current_thinking, dict):
        current_thinking = {}
    return {**_blank_thinking_profile(), **current_thinking, **thinking_patch}


def debug_enabled() -> bool:
    return os.getenv("PATHFINDER_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def require_debug_enabled() -> None:
    if not debug_enabled():
        raise HTTPException(status_code=404, detail="Not found")


def _build_debug_message(message_data: dict, index: int, queue_key: str):
    role = message_data.get("role") or message_data.get("type")
    content = message_data.get("content", "")
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False)

    if role in {"ai", "assistant"}:
        return AIMessage(content=content)
    if role == "system":
        return SystemMessage(content=content)
    if role == "tool":
        tool_call_id = str(message_data.get("tool_call_id") or f"{queue_key}-tool-{index}")
        return ToolMessage(content=content, tool_call_id=tool_call_id)
    return HumanMessage(content=content)


def _coerce_debug_patch(patch: dict) -> dict:
    coerced = {}
    for key, value in patch.items():
        if key not in QUEUE_KEYS or not isinstance(value, list):
            coerced[key] = value
            continue
        coerced[key] = [
            item if hasattr(item, "content") else _build_debug_message(item, index, key)
            for index, item in enumerate(value, start=1)
            if isinstance(item, dict) or hasattr(item, "content")
        ]
    return coerced


def _state_payload(state: dict) -> dict:
    return {
        "rawState": serialize_value(state),
        "frontendState": serialize_state(state),
    }


def serialize_state(result: dict) -> dict:
    """Map PathFinderState → frontend appState shape."""
    stage = result.get("stage") or {}
    current_stage = stage.get("current_stage", "thinking") if isinstance(stage, dict) else "thinking"
    anchor_stage = stage.get("anchor_stage", "") if isinstance(stage, dict) else ""
    anchor_mode = stage.get("anchor_mode", "normal") if isinstance(stage, dict) else "normal"
    forced_stage = anchor_stage if anchor_mode in {"forced", "revisit"} and anchor_stage != current_stage else ""
    stage_alias = {"university": "uni"}

    completed = []
    for key in ["thinking", "purpose", "goals", "job", "major", "university"]:
        profile = result.get(key)
        if isinstance(profile, dict) and profile.get("done"):
            completed.append(stage_alias.get(key, key))

    return {
        "currentStage":      stage_alias.get(current_stage, current_stage),
        "forcedStage":       stage_alias.get(forced_stage, forced_stage),
        "completedStages":   completed,
        "turn_count":        result.get("turn_count", 0),
        "thinking":          result.get("thinking"),
        "purpose":           result.get("purpose"),
        "goals":             result.get("goals"),
        "job":               result.get("job"),
        "major":             result.get("major"),
        "uni":               result.get("university"),
        "user_tag":          result.get("user_tag"),
        "escalationPending": result.get("escalation_pending", False),
    }


@app.post("/test/{session_id}")
async def test_submit(session_id: str, request: TestRequest):
    submitted_brain = "brain_type" in request.model_fields_set
    submitted_riasec = "riasec_top" in request.model_fields_set
    thinking_patch = {
        **({"brain_type": request.brain_type} if submitted_brain else {}),
        **({"riasec_top": request.riasec_top} if submitted_riasec else {}),
    }
    config = {"configurable": {"thread_id": session_id}}

    # Merge into existing thinking (may be None for new session, or partially filled by scoring)
    snapshot = await input_orchestrator.aget_state(config)
    current_thinking = snapshot.values.get("thinking")
    merged_thinking = _coerce_thinking_seed(current_thinking, thinking_patch)
    await input_orchestrator.aupdate_state(
        config,
        {"thinking": merged_thinking},
        as_node=CHECKPOINT_PATCH_NODE,
    )

    async def generate():
        yield f"data: {json.dumps({'type': 'state', 'data': {'thinking': thinking_patch, 'testStatus': {'miSubmitted': submitted_brain, 'riasecSubmitted': submitted_riasec}}})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")


_LOCKED_RESPONSE = "Cuộc trò chuyện của chúng ta đã kết thúc ở đây. Nếu em muốn tiếp tục, hãy bắt đầu một phiên mới."

@app.post("/debug/trace/{session_id}/start")
async def debug_start_trace(session_id: str):
    require_debug_enabled()
    return start_trace_session(session_id)


@app.post("/debug/trace/{session_id}/stop")
async def debug_stop_trace(session_id: str):
    require_debug_enabled()
    return stop_trace_session(session_id)


@app.get("/debug/state/{session_id}")
async def debug_get_state(session_id: str):
    require_debug_enabled()
    config = {"configurable": {"thread_id": session_id}}
    snapshot = await input_orchestrator.aget_state(config)
    return _state_payload(snapshot.values)


@app.post("/debug/state/{session_id}")
async def debug_patch_state(session_id: str, request: DebugStatePatchRequest):
    require_debug_enabled()
    config = {"configurable": {"thread_id": session_id}}
    await input_orchestrator.aupdate_state(
        config,
        _coerce_debug_patch(request.patch),
        as_node=CHECKPOINT_PATCH_NODE,
    )
    snapshot = await input_orchestrator.aget_state(config)
    return _state_payload(snapshot.values)


@app.post("/chat/{session_id}")
async def chat_stream(session_id: str, request: ChatRequest):
    config = {"configurable": {"thread_id": session_id}}

    snapshot = await input_orchestrator.aget_state(config)
    trace = LiveTraceCollector(session_id=session_id, user_message=request.message) if is_trace_active(session_id) else None
    if snapshot.values.get("escalation_pending"):
        async def locked_stream():
            yield f"data: {json.dumps({'type': 'token', 'content': _LOCKED_RESPONSE})}\n\n"
            if trace is not None:
                trace.add_token(_LOCKED_RESPONSE)
                trace.write(
                    status="success",
                    output_state=snapshot.values,
                    frontend_state=serialize_state(snapshot.values),
                )
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return StreamingResponse(locked_stream(), media_type="text/event-stream")

    state  = {"messages": [{"role": "user", "content": request.message}]}

    async def generate():
        result_state = None
        frontend_state = None
        try:
            async for event in input_orchestrator.astream_events(state, config=config, version="v2"):
                kind     = event["event"]
                metadata = event.get("metadata", {})
                node     = metadata.get("langgraph_node", "")
                if trace is not None:
                    trace.add_event(event)

                if kind == "on_chat_model_stream" and node == "output_compiler":
                    # Only stream tokens from the human-facing response node
                    token = event["data"]["chunk"].content
                    if token:
                        token = sanitize_student_stream_token(token)
                    if token:
                        if trace is not None:
                            trace.add_token(token)
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

                elif kind == "on_chain_end" and event.get("name") == "LangGraph" and not node:
                    # Only capture state from top-level graph (subgraphs have node set)
                    result_state = event["data"].get("output", {})
                    frontend_state = serialize_state(result_state)
                    yield f"data: {json.dumps({'type': 'state', 'data': frontend_state})}\n\n"

            if trace is not None:
                trace.write(
                    status="success",
                    output_state=result_state,
                    frontend_state=frontend_state,
                )
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            if trace is not None:
                trace.write(
                    status="error",
                    output_state=result_state,
                    frontend_state=frontend_state,
                    error=e,
                )
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
