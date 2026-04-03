# Current Context

Use this file as the short-lived working scratchpad for the current build cycle.
Move durable decisions to `PROJECT_CONTEXT.md` or `docs/DEV_LOG.md`.

## Active Goal
- Goal: Canonicalize the evaluation strategy for web-enabled data agents (`job`, `major`, `uni`).
- Success condition: the repo has one source-of-truth doc for retrieval-aware stage evaluation, including replay-vs-live guidance, attack categories, and trace-audit criteria.
- Deadline or milestone: 2026-04-03 evaluation-method cleanup.

## Current Workstream
- Area: Evaluation documentation and attack methodology.
- Files in play: `docs/evaluation/data_agent_evaluation.md`, `docs/evaluation/stage_evaluation.md`, `docs/DEV_LOG.md`, `docs/context/docs/CURRENT_CONTEXT.md`
- Why this matters now: `job`, `major`, and `uni` are retrieval-enabled stages, so the older pure-stage attack pattern was incomplete for search-trigger, query-quality, and evidence-grounding failures.

## Open Questions
- Question: Should the eval runner gain a first-class mocked-search seam so replay datasets can be fully deterministic?
- Blocking component: None
- Next check: Decide whether to extend `eval/run_eval.py` with fixture-backed tool injection or keep replay checks manual for now.

## Risks And Constraints
- Risk: Live web search makes eval traces unstable across time because snippets drift and numbers change.
- Evidence: the current `search` tool is backed by live Serper results, while `eval/run_eval.py` only replays input state, not tool responses.
- Mitigation: treat replay-with-frozen-tool-results as the target eval architecture and keep live-search runs as smoke checks only.

## Commands To Re-Run
- `python eval/run_eval.py --mode multi --file eval/<target_attack>.jsonl --graph <target_graph>`

## Handoff
- Latest change: Added `docs/evaluation/data_agent_evaluation.md` as the canonical guide for evaluating retrieval-enabled stage agents, and linked it from `docs/evaluation/stage_evaluation.md`.
- Verification completed: doc-only update; no code or eval runs were executed for this change.
- Next best action: write the first replay-style audit doc and attack dataset for one data agent, preferably `job`, using the new trigger/query/evidence rubric.

## Update Stamp
- Last updated: 2026-04-03
- Owner: Codex
