import json
from datetime import datetime, timezone
from pathlib import Path


SERPER_LIMIT = 2500
USAGE_PATH = Path(".cache/pathfinder/retrieval_usage.json")


def _default_usage_state() -> dict[str, int | str]:
    return {
        "serper_limit": SERPER_LIMIT,
        "serper_calls": 0,
        "updated_at": "",
    }


def load_usage_state() -> dict[str, int | str]:
    if not USAGE_PATH.exists():
        return _default_usage_state()

    try:
        raw = json.loads(USAGE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _default_usage_state()

    state = _default_usage_state()
    state.update({k: raw.get(k, v) for k, v in state.items()})
    return state


def save_usage_state(state: dict[str, int | str]) -> None:
    USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    USAGE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def can_use_serper() -> bool:
    state = load_usage_state()
    return int(state["serper_calls"]) < int(state["serper_limit"])


def mark_serper_call() -> dict[str, int | str]:
    state = load_usage_state()
    state["serper_calls"] = int(state["serper_calls"]) + 1
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_usage_state(state)
    return state

