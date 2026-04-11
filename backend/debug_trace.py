from __future__ import annotations

import json
import re
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import BaseMessage

from backend.message_window import total_message_tokens


REPO_ROOT = Path(__file__).resolve().parent.parent
THREADS_DIR = REPO_ROOT / "eval" / "threads"
TRACE_DIR_NAME = "traces"

_ACTIVE_TRACE_SESSIONS: set[str] = set()


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def safe_session_id(session_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", session_id.strip())
    return cleaned or "debug-session"


def session_dir(session_id: str, threads_dir: Path = THREADS_DIR) -> Path:
    return threads_dir / safe_session_id(session_id)


def trace_dir(session_id: str, threads_dir: Path = THREADS_DIR) -> Path:
    return session_dir(session_id, threads_dir=threads_dir) / TRACE_DIR_NAME


def manifest_path(session_id: str, threads_dir: Path = THREADS_DIR) -> Path:
    return session_dir(session_id, threads_dir=threads_dir) / "live_session.json"


def serialize_message(message: BaseMessage) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": getattr(message, "type", message.__class__.__name__),
        "content": serialize_value(getattr(message, "content", "")),
    }
    for field_name in ("id", "name", "tool_call_id", "status"):
        value = getattr(message, field_name, None)
        if value not in (None, ""):
            payload[field_name] = value
    for field_name in (
        "additional_kwargs",
        "response_metadata",
        "usage_metadata",
        "tool_calls",
        "invalid_tool_calls",
        "artifact",
    ):
        value = getattr(message, field_name, None)
        if value not in (None, "", {}, []):
            payload[field_name] = serialize_value(value)
    return payload


def serialize_value(value: Any) -> Any:
    if isinstance(value, BaseMessage):
        return serialize_message(value)
    if hasattr(value, "model_dump"):
        return serialize_value(value.model_dump())
    if isinstance(value, dict):
        return {str(key): serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [serialize_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(default)
    return raw if isinstance(raw, dict) else dict(default)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _default_manifest(session_id: str) -> dict[str, Any]:
    return {
        "trace_source": "frontend_live",
        "thread_id": session_id,
        "active": False,
        "started_at": "",
        "stopped_at": "",
        "trace_count": 0,
        "traces": [],
        "token_totals": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "approx_context_tokens": 0,
        },
    }


def start_trace_session(session_id: str, threads_dir: Path = THREADS_DIR) -> dict[str, Any]:
    path = manifest_path(session_id, threads_dir=threads_dir)
    manifest = _read_json(path, _default_manifest(session_id))
    manifest.update(
        {
            "trace_source": "frontend_live",
            "thread_id": session_id,
            "active": True,
            "started_at": manifest.get("started_at") or _now_iso(),
            "stopped_at": "",
        }
    )
    manifest.setdefault("traces", [])
    manifest.setdefault("token_totals", _default_manifest(session_id)["token_totals"])
    _write_json(path, manifest)
    _ACTIVE_TRACE_SESSIONS.add(session_id)
    return manifest


def stop_trace_session(session_id: str, threads_dir: Path = THREADS_DIR) -> dict[str, Any]:
    path = manifest_path(session_id, threads_dir=threads_dir)
    manifest = _read_json(path, _default_manifest(session_id))
    manifest.update(
        {
            "trace_source": "frontend_live",
            "thread_id": session_id,
            "active": False,
            "stopped_at": _now_iso(),
        }
    )
    _write_json(path, manifest)
    _ACTIVE_TRACE_SESSIONS.discard(session_id)
    return manifest


def is_trace_active(session_id: str, threads_dir: Path = THREADS_DIR) -> bool:
    if session_id in _ACTIVE_TRACE_SESSIONS:
        return True
    manifest = _read_json(manifest_path(session_id, threads_dir=threads_dir), {})
    if manifest.get("active") is True:
        _ACTIVE_TRACE_SESSIONS.add(session_id)
        return True
    return False


def _next_run_index(session_id: str, threads_dir: Path = THREADS_DIR) -> int:
    folder = trace_dir(session_id, threads_dir=threads_dir)
    if not folder.exists():
        return 1
    indices: list[int] = []
    for path in folder.glob("live_*.json"):
        try:
            indices.append(int(path.stem.split("_", 1)[1]))
        except (IndexError, ValueError):
            continue
    return max(indices, default=0) + 1


def _usage_from_mapping(raw: Any) -> dict[str, int] | None:
    if not isinstance(raw, dict):
        return None

    input_tokens = (
        raw.get("input_tokens")
        or raw.get("prompt_tokens")
        or raw.get("input_token_count")
        or 0
    )
    output_tokens = (
        raw.get("output_tokens")
        or raw.get("completion_tokens")
        or raw.get("output_token_count")
        or 0
    )
    total_tokens = raw.get("total_tokens") or raw.get("total_token_count") or 0

    try:
        input_tokens = int(input_tokens or 0)
        output_tokens = int(output_tokens or 0)
        total_tokens = int(total_tokens or input_tokens + output_tokens)
    except (TypeError, ValueError):
        return None

    if input_tokens == 0 and output_tokens == 0 and total_tokens == 0:
        return None
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def _usage_from_output(output: Any) -> dict[str, int] | None:
    usage = getattr(output, "usage_metadata", None)
    parsed = _usage_from_mapping(usage)
    if parsed is not None:
        return parsed

    metadata = getattr(output, "response_metadata", None)
    if isinstance(metadata, dict):
        parsed = _usage_from_mapping(metadata.get("token_usage"))
        if parsed is not None:
            return parsed
        parsed = _usage_from_mapping(metadata.get("usage"))
        if parsed is not None:
            return parsed

    if isinstance(output, dict):
        parsed = _usage_from_mapping(output.get("usage_metadata"))
        if parsed is not None:
            return parsed
        parsed = _usage_from_mapping(output.get("response_metadata", {}).get("token_usage"))
        if parsed is not None:
            return parsed
    return None


def _collect_messages(value: Any) -> list[BaseMessage]:
    if isinstance(value, BaseMessage):
        return [value]
    if isinstance(value, dict):
        found: list[BaseMessage] = []
        for item in value.values():
            found.extend(_collect_messages(item))
        return found
    if isinstance(value, (list, tuple)):
        found: list[BaseMessage] = []
        for item in value:
            found.extend(_collect_messages(item))
        return found
    return []


def approximate_tokens_from_event_input(value: Any) -> int:
    messages = _collect_messages(value)
    if messages:
        return total_message_tokens(messages)
    if isinstance(value, str):
        return max(1, len(value) // 4)
    if value is None:
        return 0
    return max(1, len(json.dumps(serialize_value(value), ensure_ascii=False)) // 4)


def _model_from_event(event: dict[str, Any], output: Any = None) -> str:
    metadata = event.get("metadata") or {}
    invocation = {}
    data = event.get("data") or {}
    if isinstance(data, dict):
        invocation = data.get("invocation_params") or {}
    if isinstance(invocation, dict):
        model = invocation.get("model") or invocation.get("model_name")
        if model:
            return str(model)
    response_metadata = getattr(output, "response_metadata", None)
    if isinstance(response_metadata, dict):
        model = response_metadata.get("model_name") or response_metadata.get("model")
        if model:
            return str(model)
    return str(metadata.get("ls_model_name") or metadata.get("model") or "")


def _node_from_event(event: dict[str, Any]) -> str:
    metadata = event.get("metadata") or {}
    return str(metadata.get("langgraph_node") or event.get("name") or "")


def token_row_from_event(
    event: dict[str, Any],
    approx_context_tokens: int,
) -> dict[str, Any] | None:
    if event.get("event") != "on_chat_model_end":
        return None

    data = event.get("data") or {}
    output = data.get("output") if isinstance(data, dict) else None
    usage = _usage_from_output(output)
    if usage is not None:
        return {
            "node": _node_from_event(event),
            "model": _model_from_event(event, output=output),
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "total_tokens": usage["total_tokens"],
            "approx_context_tokens": approx_context_tokens,
            "source": "provider",
        }

    return {
        "node": _node_from_event(event),
        "model": _model_from_event(event, output=output),
        "input_tokens": approx_context_tokens,
        "output_tokens": 0,
        "total_tokens": approx_context_tokens,
        "approx_context_tokens": approx_context_tokens,
        "source": "approx",
    }


def _token_totals(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "input_tokens": sum(int(row.get("input_tokens") or 0) for row in rows),
        "output_tokens": sum(int(row.get("output_tokens") or 0) for row in rows),
        "total_tokens": sum(int(row.get("total_tokens") or 0) for row in rows),
        "approx_context_tokens": sum(int(row.get("approx_context_tokens") or 0) for row in rows),
    }


@dataclass
class LiveTraceCollector:
    session_id: str
    user_message: str
    frontend_state: dict[str, Any] | None = None
    threads_dir: Path = THREADS_DIR
    run_index: int = field(init=False)
    started_at: str = field(default_factory=_now_iso)
    assistant_text: str = ""
    timeline: list[dict[str, Any]] = field(default_factory=list)
    token_rows: list[dict[str, Any]] = field(default_factory=list)
    _approx_by_run_id: dict[str, int] = field(default_factory=dict)
    _seen_token_runs: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.run_index = _next_run_index(self.session_id, threads_dir=self.threads_dir)

    def add_token(self, content: str) -> None:
        self.assistant_text += content

    def add_event(self, event: dict[str, Any]) -> None:
        kind = event.get("event", "")
        metadata = event.get("metadata") or {}
        run_id = str(event.get("run_id") or "")
        node = str(metadata.get("langgraph_node") or "")
        name = str(event.get("name") or "")

        self.timeline.append(
            {
                "index": len(self.timeline) + 1,
                "event": kind,
                "name": name,
                "node": node,
                "run_id": run_id,
            }
        )

        if kind == "on_chat_model_start":
            data = event.get("data") or {}
            approx = approximate_tokens_from_event_input(
                data.get("input") if isinstance(data, dict) else data
            )
            if run_id:
                self._approx_by_run_id[run_id] = approx
            return

        if kind == "on_chat_model_end":
            approx = self._approx_by_run_id.get(run_id, 0)
            row = token_row_from_event(event, approx_context_tokens=approx)
            if row is not None:
                self.token_rows.append(row)
                if run_id:
                    self._seen_token_runs.add(run_id)

    def write(
        self,
        *,
        status: str,
        output_state: dict[str, Any] | None,
        frontend_state: dict[str, Any] | None,
        error: BaseException | None = None,
    ) -> Path:
        for run_id, approx in self._approx_by_run_id.items():
            if run_id not in self._seen_token_runs:
                self.token_rows.append(
                    {
                        "node": "",
                        "model": "",
                        "input_tokens": approx,
                        "output_tokens": 0,
                        "total_tokens": approx,
                        "approx_context_tokens": approx,
                        "source": "approx",
                    }
                )

        payload: dict[str, Any] = {
            "trace_source": "frontend_live",
            "thread_id": self.session_id,
            "trace_id": f"live_{self.run_index:04d}",
            "run_index": self.run_index,
            "started_at": self.started_at,
            "finished_at": _now_iso(),
            "status": status,
            "input": {"message": self.user_message},
            "assistant_text": self.assistant_text,
            "event_timeline": self.timeline,
            "token_rows": self.token_rows,
            "token_totals": _token_totals(self.token_rows),
            "output": serialize_value(output_state),
            "frontend_state": serialize_value(frontend_state),
        }

        if error is not None:
            payload["error"] = {
                "type": error.__class__.__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            }

        folder = trace_dir(self.session_id, threads_dir=self.threads_dir)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"live_{self.run_index:04d}.json"
        _write_json(path, payload)
        update_manifest_after_trace(self.session_id, path, payload, threads_dir=self.threads_dir)
        return path


def update_manifest_after_trace(
    session_id: str,
    trace_path: Path,
    trace_payload: dict[str, Any],
    threads_dir: Path = THREADS_DIR,
) -> dict[str, Any]:
    path = manifest_path(session_id, threads_dir=threads_dir)
    manifest = _read_json(path, _default_manifest(session_id))
    traces = list(manifest.get("traces") or [])
    relative_path = str(trace_path.relative_to(REPO_ROOT)) if trace_path.is_relative_to(REPO_ROOT) else str(trace_path)
    if relative_path not in traces:
        traces.append(relative_path)
    token_totals = dict(manifest.get("token_totals") or _default_manifest(session_id)["token_totals"])
    for key, value in (trace_payload.get("token_totals") or {}).items():
        token_totals[key] = int(token_totals.get(key) or 0) + int(value or 0)
    manifest.update(
        {
            "trace_source": "frontend_live",
            "thread_id": session_id,
            "trace_count": len(traces),
            "traces": traces,
            "token_totals": token_totals,
            "last_trace_at": trace_payload.get("finished_at") or _now_iso(),
        }
    )
    _write_json(path, manifest)
    return manifest
