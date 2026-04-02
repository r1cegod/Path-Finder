from __future__ import annotations

import argparse
import copy
import importlib
import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

from backend.data.state import DEFAULT_STAGE, DEFAULT_STATE

EVAL_DIR = REPO_ROOT / "eval"
THREADS_DIR = EVAL_DIR / "threads"
TRACE_DIR_NAME = "traces"


@dataclass(frozen=True)
class GraphSpec:
    key: str
    module_path: str
    graph_attr: str
    default_queue: str
    current_stage: str | None


@dataclass(frozen=True)
class RunOutcome:
    run_index: int
    thread_id: str
    status: str
    trace_path: Path
    error_message: str | None = None


CANONICAL_GRAPHS: dict[str, GraphSpec] = {
    "thinking": GraphSpec(
        key="thinking",
        module_path="backend.thinking_graph",
        graph_attr="thinking_graph",
        default_queue="thinking_style_message",
        current_stage="thinking",
    ),
    "purpose": GraphSpec(
        key="purpose",
        module_path="backend.purpose_graph",
        graph_attr="purpose_graph",
        default_queue="purpose_message",
        current_stage="purpose",
    ),
    "goals": GraphSpec(
        key="goals",
        module_path="backend.goals_graph",
        graph_attr="goals_graph",
        default_queue="goals_message",
        current_stage="goals",
    ),
    "job": GraphSpec(
        key="job",
        module_path="backend.job_graph",
        graph_attr="job_graph",
        default_queue="job_message",
        current_stage="job",
    ),
    "major": GraphSpec(
        key="major",
        module_path="backend.major_graph",
        graph_attr="major_graph",
        default_queue="major_message",
        current_stage="major",
    ),
    "uni": GraphSpec(
        key="uni",
        module_path="backend.uni_graph",
        graph_attr="uni_graph",
        default_queue="uni_message",
        current_stage="university",
    ),
    "output": GraphSpec(
        key="output",
        module_path="backend.output_graph",
        graph_attr="output_graph",
        default_queue="messages",
        current_stage=None,
    ),
    "orchestrator": GraphSpec(
        key="orchestrator",
        module_path="backend.orchestrator_graph",
        graph_attr="input_orchestrator",
        default_queue="messages",
        current_stage=None,
    ),
}

GRAPH_ALIASES = {
    "thinking_graph": "thinking",
    "purpose_graph": "purpose",
    "goals_graph": "goals",
    "job_graph": "job",
    "major_graph": "major",
    "uni_graph": "uni",
    "university": "uni",
    "university_graph": "uni",
    "output_graph": "output",
    "input_orchestrator": "orchestrator",
    "orchestrator_graph": "orchestrator",
}

QUEUE_KEYS = (
    "messages",
    "thinking_style_message",
    "purpose_message",
    "goals_message",
    "job_message",
    "major_message",
    "uni_message",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a JSONL eval dataset through a PathFinder graph."
    )
    parser.add_argument("--mode", choices=("single", "multi"), required=True)
    parser.add_argument("--file", required=True, help="Path to a JSONL file inside eval/.")
    parser.add_argument(
        "--graph",
        required=True,
        help=(
            "Graph name or alias, for example: thinking, purpose, goals, job, major, "
            "uni, output, orchestrator, purpose_graph, input_orchestrator."
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Worker count for multi mode. Defaults to min(8, number of inputs).",
    )
    return parser.parse_args()


def resolve_input_file(file_arg: str) -> Path:
    file_path = Path(file_arg)
    resolved = (
        (REPO_ROOT / file_path).resolve() if not file_path.is_absolute() else file_path.resolve()
    )

    if resolved.suffix.lower() != ".jsonl":
        raise ValueError("--file must point to a .jsonl file.")
    if not resolved.is_file():
        raise FileNotFoundError(f"Input file not found: {resolved}")

    try:
        resolved.relative_to(EVAL_DIR)
    except ValueError as exc:
        raise ValueError(f"--file must point to a JSONL file inside {EVAL_DIR}") from exc

    return resolved


def resolve_graph(graph_name: str) -> GraphSpec:
    normalized = graph_name.strip().lower()
    canonical = GRAPH_ALIASES.get(normalized, normalized)
    spec = CANONICAL_GRAPHS.get(canonical)
    if spec is None:
        supported = ", ".join(sorted(CANONICAL_GRAPHS))
        raise ValueError(f"Unsupported graph '{graph_name}'. Supported graphs: {supported}")
    return spec


def load_graph(spec: GraphSpec):
    module = importlib.import_module(spec.module_path)
    return getattr(module, spec.graph_attr)


def load_jsonl_inputs(file_path: Path) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []

    with file_path.open("r", encoding="utf-8-sig") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                parsed = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} in {file_path}") from exc

            if not isinstance(parsed, dict):
                raise ValueError(f"Line {line_number} in {file_path} must be a JSON object.")

            inputs.append(parsed)

    if not inputs:
        raise ValueError(f"No JSON objects found in {file_path}")

    return inputs


def build_message(message_data: dict[str, Any], index: int, queue_key: str) -> BaseMessage:
    role = message_data.get("role")
    if role not in {"assistant", "system", "tool", "user"}:
        raise ValueError(
            f"Unsupported role '{role}' in '{queue_key}' at message index {index}. "
            "Expected assistant, system, tool, or user."
        )

    content = message_data.get("content", "")
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False)

    if role == "assistant":
        return AIMessage(content=content)
    if role == "system":
        return SystemMessage(content=content)
    if role == "tool":
        tool_call_id = str(message_data.get("tool_call_id") or f"{queue_key}-tool-{index}")
        return ToolMessage(content=content, tool_call_id=tool_call_id)
    return HumanMessage(content=content)


def build_message_list(raw_messages: Any, queue_key: str) -> list[BaseMessage]:
    if not isinstance(raw_messages, list):
        raise ValueError(f"'{queue_key}' must be a list of message objects.")

    messages: list[BaseMessage] = []
    for index, message_data in enumerate(raw_messages, start=1):
        if isinstance(message_data, BaseMessage):
            messages.append(message_data)
            continue
        if not isinstance(message_data, dict):
            raise ValueError(f"'{queue_key}' message #{index} must be an object with role/content.")
        messages.append(build_message(message_data, index=index, queue_key=queue_key))
    return messages


def build_state_for_graph(raw_input: dict[str, Any], spec: GraphSpec) -> dict[str, Any]:
    state = copy.deepcopy(DEFAULT_STATE)
    state["stage"] = copy.deepcopy(DEFAULT_STAGE)
    discovered_queues: list[str] = []

    for key, value in raw_input.items():
        if key == "stage":
            if value is None:
                continue
            if not isinstance(value, dict):
                raise ValueError("'stage' must be a JSON object.")
            merged_stage = copy.deepcopy(DEFAULT_STAGE)
            merged_stage.update(copy.deepcopy(value))
            state["stage"] = merged_stage
            continue

        if key in QUEUE_KEYS:
            state[key] = build_message_list(value, queue_key=key)
            discovered_queues.append(key)
            continue

        state[key] = copy.deepcopy(value)

    if spec.current_stage is not None:
        raw_stage = raw_input.get("stage")
        if not (isinstance(raw_stage, dict) and "current_stage" in raw_stage):
            stage_state = copy.deepcopy(state.get("stage") or DEFAULT_STAGE)
            stage_state["current_stage"] = spec.current_stage
            state["stage"] = stage_state

    if spec.default_queue not in discovered_queues:
        fallback_messages: list[BaseMessage] | None = None

        if "messages" in raw_input and spec.default_queue != "messages":
            fallback_messages = copy.deepcopy(state["messages"])
        elif spec.default_queue == "messages" and len(discovered_queues) == 1:
            fallback_messages = copy.deepcopy(state[discovered_queues[0]])
        elif len(discovered_queues) == 1:
            fallback_messages = copy.deepcopy(state[discovered_queues[0]])

        if fallback_messages is not None:
            state[spec.default_queue] = fallback_messages

    if not state.get(spec.default_queue):
        raise ValueError(
            f"No conversation queue found for graph '{spec.graph_attr}'. Expected "
            f"'{spec.default_queue}' or a compatible single queue in the input row."
        )

    return state


def serialize_message(message: BaseMessage) -> dict[str, Any]:
    payload = {
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


def write_trace(trace: dict[str, Any], thread_id: str, run_index: int) -> Path:
    trace_dir = THREADS_DIR / thread_id / TRACE_DIR_NAME
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_path = trace_dir / f"run_{run_index:04d}.json"
    trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
    return trace_path


def run_one_input(
    graph: Any,
    spec: GraphSpec,
    raw_input: dict[str, Any],
    file_path: Path,
    run_index: int,
    thread_id: str,
    mode: str,
) -> RunOutcome:
    timestamp = datetime.now().astimezone().isoformat()
    trace: dict[str, Any] = {
        "graph_name": spec.graph_attr,
        "graph_key": spec.key,
        "graph_module": spec.module_path,
        "input_file": str(file_path.relative_to(REPO_ROOT)),
        "mode": mode,
        "run_index": run_index,
        "thread_id": thread_id,
        "timestamp": timestamp,
        "input": serialize_value(raw_input),
        "output": None,
        "status": "success",
    }

    try:
        normalized_input = build_state_for_graph(raw_input=raw_input, spec=spec)
        trace["normalized_input"] = serialize_value(normalized_input)

        config = {"configurable": {"thread_id": thread_id}}
        result_state = graph.invoke(normalized_input, config=config)
        trace["output"] = serialize_value(result_state)
    except Exception as exc:
        trace["status"] = "error"
        trace["output"] = {
            "error_type": exc.__class__.__name__,
            "error_message": str(exc),
        }
        trace["error_traceback"] = traceback.format_exc()

    trace_path = write_trace(trace=trace, thread_id=thread_id, run_index=run_index)
    error_message = None
    if trace["status"] == "error":
        error_message = trace["output"]["error_message"]

    return RunOutcome(
        run_index=run_index,
        thread_id=thread_id,
        status=trace["status"],
        trace_path=trace_path,
        error_message=error_message,
    )


def print_outcome(outcome: RunOutcome) -> None:
    relative_trace_path = outcome.trace_path.relative_to(REPO_ROOT)
    if outcome.status == "success":
        print(
            f"[{outcome.run_index:04d}] ok     "
            f"thread={outcome.thread_id} trace={relative_trace_path}"
        )
        return
    print(
        f"[{outcome.run_index:04d}] error  thread={outcome.thread_id} "
        f"trace={relative_trace_path} reason={outcome.error_message}"
    )


def run_single_mode(
    graph: Any,
    spec: GraphSpec,
    inputs: list[dict[str, Any]],
    file_path: Path,
) -> list[RunOutcome]:
    shared_thread_id = str(uuid4())
    print(f"Single thread_id: {shared_thread_id}")

    outcomes: list[RunOutcome] = []
    for run_index, raw_input in enumerate(inputs, start=1):
        outcome = run_one_input(
            graph=graph,
            spec=spec,
            raw_input=raw_input,
            file_path=file_path,
            run_index=run_index,
            thread_id=shared_thread_id,
            mode="single",
        )
        outcomes.append(outcome)
        print_outcome(outcome)

    return outcomes


def run_multi_mode(
    graph: Any,
    spec: GraphSpec,
    inputs: list[dict[str, Any]],
    file_path: Path,
    workers: int | None,
) -> list[RunOutcome]:
    max_workers = workers or min(8, len(inputs))
    if max_workers < 1:
        raise ValueError("--workers must be >= 1.")

    print(f"Workers: {max_workers}")

    outcomes: list[RunOutcome] = []
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="eval") as executor:
        future_map = {
            executor.submit(
                run_one_input,
                graph,
                spec,
                raw_input,
                file_path,
                run_index,
                str(uuid4()),
                "multi",
            ): run_index
            for run_index, raw_input in enumerate(inputs, start=1)
        }

        for future in as_completed(future_map):
            outcome = future.result()
            outcomes.append(outcome)
            print_outcome(outcome)

    outcomes.sort(key=lambda item: item.run_index)
    return outcomes


def main() -> None:
    args = parse_args()
    file_path = resolve_input_file(args.file)
    spec = resolve_graph(args.graph)
    inputs = load_jsonl_inputs(file_path)
    graph = load_graph(spec)

    THREADS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"File: {file_path.relative_to(REPO_ROOT)}")
    print(f"Graph: {spec.module_path}.{spec.graph_attr}")
    print(f"Mode: {args.mode}")
    print(f"Inputs: {len(inputs)}")

    if args.mode == "single":
        outcomes = run_single_mode(graph=graph, spec=spec, inputs=inputs, file_path=file_path)
    else:
        outcomes = run_multi_mode(
            graph=graph,
            spec=spec,
            inputs=inputs,
            file_path=file_path,
            workers=args.workers,
        )

    success_count = sum(1 for outcome in outcomes if outcome.status == "success")
    failure_count = len(outcomes) - success_count

    print(f"Success: {success_count}")
    print(f"Failed: {failure_count}")

    if failure_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
