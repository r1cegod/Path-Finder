"""Small CLI for live PathFinder evaluation sessions.

This is for human-like frontend/debug evaluation where replaying the whole
thread is wasteful. Prefer `--message-file` for Vietnamese input; passing
non-ASCII literals through PowerShell pipes can corrupt accents before Python
receives them.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
STAGE_ORDER = ("thinking", "purpose", "goals", "job", "major", "uni")


def _read_text_arg(value: str | None, file_path: str | None) -> str:
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    if value is None:
        raise SystemExit("Provide --message or --message-file.")
    return value


def _request(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: int = 180,
) -> str:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} from {url}\n{body}") from exc


def _request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: int = 180,
) -> dict[str, Any]:
    text = _request(method, url, payload, timeout=timeout)
    return json.loads(text)


def _parse_sse(text: str) -> tuple[str, dict[str, Any] | None, list[str]]:
    assistant: list[str] = []
    state: dict[str, Any] | None = None
    errors: list[str] = []
    for chunk in text.split("\n\n"):
        lines = [line[5:].lstrip() for line in chunk.splitlines() if line.startswith("data:")]
        if not lines:
            continue
        event = json.loads("\n".join(lines))
        event_type = event.get("type")
        if event_type == "token":
            assistant.append(event.get("content", ""))
        elif event_type == "state":
            state = event.get("data")
        elif event_type == "error":
            errors.append(str(event.get("content", "")))
    return "".join(assistant), state, errors


def _field(entry: Any) -> Any:
    if isinstance(entry, dict):
        return {
            "content": entry.get("content"),
            "confidence": entry.get("confidence"),
        }
    return entry


def compact_state(state: dict[str, Any] | None) -> dict[str, Any] | None:
    if state is None:
        return None
    if isinstance(state.get("frontendState"), dict):
        state = state["frontendState"]
    result: dict[str, Any] = {
        "currentStage": state.get("currentStage"),
        "forcedStage": state.get("forcedStage"),
        "completedStages": state.get("completedStages"),
        "turn_count": state.get("turn_count"),
    }
    for stage in STAGE_ORDER:
        profile = state.get(stage)
        if not isinstance(profile, dict):
            continue
        stage_summary: dict[str, Any] = {"done": profile.get("done")}
        if stage == "goals":
            long_profile = profile.get("long") or {}
            short_profile = profile.get("short") or {}
            stage_summary["long"] = {
                "done": long_profile.get("done"),
                "income_target": _field(long_profile.get("income_target")),
                "autonomy_level": _field(long_profile.get("autonomy_level")),
                "ownership_model": _field(long_profile.get("ownership_model")),
                "team_size": _field(long_profile.get("team_size")),
            }
            stage_summary["short"] = {
                "done": short_profile.get("done"),
                "skill_targets": _field(short_profile.get("skill_targets")),
                "portfolio_goal": _field(short_profile.get("portfolio_goal")),
                "credential_needed": _field(short_profile.get("credential_needed")),
            }
        result[stage] = stage_summary
    return result


def _print_result(payload: dict[str, Any], *, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    assistant = payload.get("assistant")
    if assistant:
        print("\nASSISTANT\n" + assistant)
    if payload.get("errors"):
        print("\nERRORS\n" + json.dumps(payload["errors"], ensure_ascii=False, indent=2))
    state = payload.get("state")
    if state is not None:
        print("\nSTATE\n" + json.dumps(state, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_send(args: argparse.Namespace) -> None:
    message = _read_text_arg(args.message, args.message_file)
    text = _request(
        "POST",
        f"{args.base_url}/chat/{args.session_id}",
        {"message": message},
        timeout=args.timeout,
    )
    assistant, state, errors = _parse_sse(text)
    _print_result(
        {
            "assistant": assistant,
            "errors": errors,
            "state": compact_state(state),
        },
        json_mode=args.json,
    )


def command_state(args: argparse.Namespace) -> None:
    state = _request_json("GET", f"{args.base_url}/debug/state/{args.session_id}", timeout=args.timeout)
    payload: dict[str, Any] = compact_state(state) if args.compact else state
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_restore(args: argparse.Namespace) -> None:
    trace = json.loads(Path(args.trace).read_text(encoding="utf-8"))
    patch = trace.get(args.state_key)
    if not isinstance(patch, dict):
        raise SystemExit(f"Trace does not contain object state key: {args.state_key}")
    state = _request_json(
        "POST",
        f"{args.base_url}/debug/state/{args.session_id}",
        {"patch": patch},
        timeout=args.timeout,
    )
    payload: dict[str, Any] = compact_state(state) if args.compact else state
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_trace(args: argparse.Namespace) -> None:
    state = _request_json(
        "POST",
        f"{args.base_url}/debug/trace/{args.session_id}/{args.action}",
        timeout=args.timeout,
    )
    print(json.dumps(state, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe live PathFinder sessions with compact state output.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=int, default=180)
    subparsers = parser.add_subparsers(dest="command", required=True)

    send = subparsers.add_parser("send", help="Send one chat turn and print assistant plus compact state.")
    send.add_argument("session_id")
    send.add_argument("--message")
    send.add_argument("--message-file")
    send.add_argument("--json", action="store_true")
    send.set_defaults(func=command_send)

    state = subparsers.add_parser("state", help="Read debug state.")
    state.add_argument("session_id")
    state.add_argument("--full", dest="compact", action="store_false")
    state.set_defaults(func=command_state, compact=True)

    restore = subparsers.add_parser("restore", help="Restore a session from a trace state object.")
    restore.add_argument("session_id")
    restore.add_argument("--trace", required=True)
    restore.add_argument("--state-key", default="output", choices=("output", "frontend_state"))
    restore.add_argument("--full", dest="compact", action="store_false")
    restore.set_defaults(func=command_restore, compact=True)

    trace = subparsers.add_parser("trace", help="Start or stop live trace capture.")
    trace.add_argument("session_id")
    trace.add_argument("action", choices=("start", "stop"))
    trace.set_defaults(func=command_trace)

    return parser


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
