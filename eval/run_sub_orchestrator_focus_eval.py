from __future__ import annotations

import argparse
import copy
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
from langchain_core.messages import BaseMessage

load_dotenv(REPO_ROOT / ".env")

from backend.sub_orchestrator_focus_eval import FocusTarget, build_focus_eval_state
from backend.sub_orchestrator_graph import run_sub_orchestrator_focus

EVAL_DIR = REPO_ROOT / "eval"
THREADS_DIR = EVAL_DIR / "threads"
TRACE_DIR_NAME = "traces"


@dataclass(frozen=True)
class RunOutcome:
    run_index: int
    thread_id: str
    status: str
    trace_path: Path
    error_message: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a focused sub-orchestrator eval dataset without touching the main orchestrator."
    )
    parser.add_argument("--target", choices=("summarizer", "worker"), required=True)
    parser.add_argument("--file", required=True, help="Path to a JSONL file inside eval/.")
    parser.add_argument("--mode", choices=("single", "multi"), default="single")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Worker count for multi mode. Defaults to min(4, number of inputs).",
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
    target: FocusTarget,
    raw_input: dict[str, Any],
    file_path: Path,
    run_index: int,
    thread_id: str,
    mode: str,
) -> RunOutcome:
    timestamp = datetime.now().astimezone().isoformat()
    trace: dict[str, Any] = {
        "graph_name": "sub_orchestrator_focus",
        "graph_key": f"sub_orchestrator_{target}_focus",
        "graph_module": "backend.sub_orchestrator_graph",
        "focus_target": target,
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
        normalized_input, metadata = build_focus_eval_state(raw_input=copy.deepcopy(raw_input), target=target)
        trace["normalized_input"] = serialize_value(normalized_input)
        trace["eval_metadata"] = serialize_value(metadata)
        trace["output"] = serialize_value(run_sub_orchestrator_focus(normalized_input, target=target))
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
    target: FocusTarget,
    inputs: list[dict[str, Any]],
    file_path: Path,
) -> list[RunOutcome]:
    shared_thread_id = str(uuid4())
    print(f"Single thread_id: {shared_thread_id}")

    outcomes: list[RunOutcome] = []
    for run_index, raw_input in enumerate(inputs, start=1):
        outcome = run_one_input(
            target=target,
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
    target: FocusTarget,
    inputs: list[dict[str, Any]],
    file_path: Path,
    workers: int | None,
) -> list[RunOutcome]:
    max_workers = workers or min(4, len(inputs))
    if max_workers < 1:
        raise ValueError("--workers must be >= 1.")

    print(f"Workers: {max_workers}")

    outcomes: list[RunOutcome] = []
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="sub-focus-eval") as executor:
        future_map = {
            executor.submit(
                run_one_input,
                target,
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
    inputs = load_jsonl_inputs(file_path)

    THREADS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"File: {file_path.relative_to(REPO_ROOT)}")
    print(f"Target: {args.target}")
    print(f"Mode: {args.mode}")
    print(f"Inputs: {len(inputs)}")

    if args.mode == "single":
        outcomes = run_single_mode(target=args.target, inputs=inputs, file_path=file_path)
    else:
        outcomes = run_multi_mode(
            target=args.target,
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
