"""
PathFinder Evaluation Runner.

Usage:
    python -m eval.run_eval                       # run all threads
    python -m eval.run_eval --stage thinking      # run one stage
    python -m eval.run_eval --thread thinking_t1  # run one thread
    python -m eval.run_eval --stage output        # run output case threads
    python -m eval.run_eval -v                    # verbose (show profile diffs)

Thread format (JSONL):
    Line 0: {"meta": {"stage": "...", "thread_id": "...", "persona": "...",
                       "queue_key": "...", "expected": {...}}}
    Line 1+: {"role": "assistant"|"user", "content": "..."}

Output case format (JSONL):
    Line 0: {"meta": {"stage": "output", "case": "A"|"B1"|"B2"|"C",
                       "thread_id": "...", "state_overrides": {...},
                       "expected_behavior": "..."}}
    Line 1+: {"role": "assistant"|"user", "content": "..."}
"""

import argparse
import copy
import importlib
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

load_dotenv()

# ─── graph registry ───────────────────────────────────────────────────────────
GRAPH_REGISTRY = {
    "thinking": ("backend.thinking_graph", "thinking_graph"),
    "purpose":  ("backend.purpose_graph",  "purpose_graph"),
    "goals":    ("backend.goals_graph",    "goals_graph"),
    "job":      ("backend.job_graph",      "job_graph"),
    "major":    ("backend.major_graph",    "major_graph"),
    "uni":      ("backend.uni_graph",      "uni_graph"),
    "output":   ("backend.output_graph",   "output_graph"),
}

# ─── message queue per stage ──────────────────────────────────────────────────
DEFAULT_QUEUE = {
    "thinking": "thinking_style_message",
    "purpose":  "purpose_message",
    "goals":    "goals_message",
    "job":      "job_message",
    "major":    "major_message",
    "uni":      "uni_message",
    "output":   "messages",
}

# ─── which state key holds the profile for each stage ────────────────────────
PROFILE_KEY = {
    "thinking": "thinking",
    "purpose":  "purpose",
    "goals":    "goals",
    "job":      "job",
    "major":    "major",
    "uni":      "university",
    "output":   None,  # output graph → capture last AIMessage instead
}

THREADS_DIR = Path("eval/threads")
RESULTS_DIR = Path("eval/results")
RESULTS_DIR.mkdir(exist_ok=True)


# ─── helpers ──────────────────────────────────────────────────────────────────

def load_thread(path: Path) -> tuple[dict, list[tuple[str, str]]]:
    """Parse JSONL thread file → (meta dict, list of (role, content) turns)."""
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    parsed = [json.loads(line) for line in lines if line.strip()]
    meta = parsed[0]["meta"]
    turns = [(item["role"], item["content"]) for item in parsed[1:]]
    return meta, turns


def build_state(meta: dict, turns: list[tuple[str, str]]) -> dict:
    """
    Build a PathFinderState dict ready for graph.invoke().

    - Injects conversation into the correct message queue.
    - Applies any state_overrides from meta (used by output case threads).
    """
    from backend.data.state import DEFAULT_STATE, StageReasoning

    state = copy.deepcopy(DEFAULT_STATE)

    # Apply state_overrides first (output case threads set profiles, flags, etc.)
    for k, v in meta.get("state_overrides", {}).items():
        state[k] = v

    # Build LangChain message objects
    messages = []
    for role, content in turns:
        if role == "assistant":
            messages.append(AIMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))

    # Inject into the correct queue for this stage
    stage = meta["stage"]
    queue_key = meta.get("queue_key") or DEFAULT_QUEUE.get(stage, "messages")
    state[queue_key] = messages

    # Output graph also needs global messages populated
    if stage == "output":
        state["messages"] = messages

    return state


def extract_profile(result_state: dict, stage: str) -> dict:
    """Pull the extracted profile (or output message) from graph result state."""
    key = PROFILE_KEY.get(stage)

    if key is None:
        # Output graph — grab last AIMessage content
        msgs = result_state.get("messages", [])
        last_ai = next(
            (m for m in reversed(msgs) if isinstance(m, AIMessage)),
            None,
        )
        return {"output_message": last_ai.content if last_ai else ""}

    raw = result_state.get(key)
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if hasattr(raw, "model_dump"):
        return raw.model_dump()
    return {}


def load_graph(stage: str):
    """Lazy-import and return the compiled LangGraph for this stage."""
    module_name, graph_attr = GRAPH_REGISTRY[stage]
    module = importlib.import_module(module_name)
    return getattr(module, graph_attr)


# ─── core runner ──────────────────────────────────────────────────────────────

def run_thread(thread_path: Path, verbose: bool = False) -> dict:
    """
    Run one thread through its graph, evaluate with Gemini, return result dict.

    Result shape:
        {
            "thread_id": str,
            "stage": str,
            "persona": str,
            "scores": {field_extraction, confidence_calibration, ...},
            "actual_profile": dict,
            "expected_profile": dict,
        }
    """
    from eval.gemini_eval import evaluate_stage, evaluate_output

    meta, turns = load_thread(thread_path)
    stage = meta["stage"]
    thread_id = meta["thread_id"]

    if verbose:
        print(f"  Loading graph for stage='{stage}' ...")

    graph = load_graph(stage)
    state = build_state(meta, turns)
    config = {"configurable": {"thread_id": thread_id}}

    if verbose:
        print(f"  Invoking graph ...")

    result_state = graph.invoke(state, config)
    actual_profile = extract_profile(result_state, stage)

    if verbose:
        print(f"  Profile keys: {list(actual_profile.keys())}")
        print(f"  Calling Gemini evaluator ...")

    if stage == "output":
        # Output graph eval uses a different rubric
        case = meta.get("case", "?")
        state_snapshot = {
            k: meta.get("state_overrides", {}).get(k)
            for k in ["bypass_stage", "path_debate_ready", "terminate",
                      "thinking", "purpose", "goals", "job", "major", "university"]
        }
        scores = evaluate_output(
            case=case,
            state_snapshot=state_snapshot,
            actual_output=actual_profile.get("output_message", ""),
            expected_behavior=meta.get("expected_behavior", ""),
        )
    else:
        scores = evaluate_stage(
            stage=stage,
            persona=meta.get("persona", "unknown"),
            conversation=turns,
            expected_profile=meta.get("expected", {}),
            actual_profile=actual_profile,
        )

    return {
        "thread_id": thread_id,
        "stage": stage,
        "persona": meta.get("persona", meta.get("case", "?")),
        "scores": scores,
        "actual_profile": actual_profile,
        "expected_profile": meta.get("expected", meta.get("expected_behavior", "")),
    }


# ─── CLI entrypoint ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PathFinder evaluation runner")
    parser.add_argument("--stage",  help="Run only this stage (e.g. thinking, output)")
    parser.add_argument("--thread", help="Run only this thread ID (e.g. thinking_t1)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print per-step details")
    args = parser.parse_args()

    thread_files = sorted(THREADS_DIR.glob("*.jsonl"))

    if args.stage:
        thread_files = [f for f in thread_files if f.stem.startswith(args.stage)]
    if args.thread:
        thread_files = [f for f in thread_files if f.stem == args.thread]

    if not thread_files:
        print(f"No thread files found in {THREADS_DIR}/")
        print("Expected naming: <stage>_t1.jsonl, <stage>_t2.jsonl, output_caseA.jsonl, ...")
        sys.exit(1)

    print(f"\nPathFinder Eval — {len(thread_files)} thread(s)\n{'─'*50}")
    all_results = []

    for tf in thread_files:
        label = tf.stem
        print(f"\n[{label}]")
        try:
            result = run_thread(tf, verbose=args.verbose)
            s = result["scores"]
            overall = s.get("overall", "?")
            notes = s.get("notes", "")
            print(f"  overall={overall}/10")
            print(f"  notes: {notes}")
            if args.verbose:
                for k, v in s.items():
                    if k not in ("overall", "notes"):
                        print(f"    {k:<30} {v}/10")
            all_results.append(result)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            all_results.append({"thread_id": tf.stem, "error": str(exc)})

    # ─── save results ─────────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"eval_{timestamp}.json"
    out_path.write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # ─── summary table ────────────────────────────────────────────────────────
    print(f"\n{'─'*50}")
    print(f"{'Thread':<28} {'Overall':>7}  {'Persona':<12}")
    print("─" * 50)
    for r in all_results:
        if "error" in r:
            print(f"{r['thread_id']:<28} {'ERR':>7}  {'':12}")
        else:
            score = r["scores"].get("overall", "?")
            persona = r.get("persona", "")
            print(f"{r['thread_id']:<28} {str(score)+'/10':>7}  {persona:<12}")

    print(f"\nResults → {out_path}\n")


if __name__ == "__main__":
    main()
