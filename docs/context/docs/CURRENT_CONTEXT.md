# Current Context

Use this file as the short-lived working scratchpad for the current build cycle.
Move durable decisions to `PROJECT_CONTEXT.md` or `docs/DEV_LOG.md`.

## Active Goal
- Goal: Finalize the backend runtime contract cleanup so the tree is ready to commit.
- Success condition: only the root orchestrator owns a checkpointer, stage queues capture both student and assistant turns where intended, and the test surface passes cleanly.
- Deadline or milestone: 2026-04-02 pre-commit cleanup.

## Current Workstream
- Area: Backend runtime contract cleanup.
- Files in play: `backend/output_graph.py`, `backend/orchestrator_graph.py`, `backend/thinking_graph.py`, `backend/purpose_graph.py`, `backend/goals_graph.py`, `backend/job_graph.py`, `backend/major_graph.py`, `backend/uni_graph.py`, `test_output_graph_contract.py`, `test_stage_contract.py`, `test_output_prompt_contract.py`, `test.py`, `docs/architecture/docs/state_architecture.md`, `docs/architecture/docs/ARCHITECTURE.md`, `docs/DEV_LOG.md`
- Why this matters now: The runtime contract is mostly stable now; the remaining pre-commit risk was stale test coverage around output tagging and import-time execution in `test.py`.

## Open Questions
- Question: Should stage queues keep only conversational turns, or should tool-call traffic also be filtered before append?
- Blocking component: None
- Next check: Inspect whether tool-enabled stages are accumulating internal tool messages in a way that hurts downstream prompts.

## Risks And Constraints
- Risk: Stage queues now capture both sides of the conversation, which is correct for context, but they may also need message-type filtering later if tool chatter becomes noisy.
- Evidence: Tool-enabled stages (`job`, `major`, `university`) already use queue-backed tool routing, so queue hygiene matters more now.
- Mitigation: Keep output tagging limited to context stages and lock the behavior with focused contract tests.

## Commands To Re-Run
- `python test.py`
- `python -m unittest test_output_prompt_contract.py`
- `python -m unittest test_stage_contract.py`
- `python -m unittest test_output_graph_contract.py`
- `langgraph dev`
- `python -c "from backend.orchestrator_graph import input_orchestrator; print('OK')"`

## Handoff
- Latest change: Kept output-side tagging limited to `stage_related` by design, updated `test_output_graph_contract.py` to lock that behavior, and moved `test.py` execution under `if __name__ == "__main__"` so `python -m unittest` no longer makes live API calls during discovery.
- Verification completed: `python -m unittest test_output_prompt_contract.py test_stage_contract.py test_output_graph_contract.py`, `python -m unittest`, and direct imports of orchestrator/output/all stage graphs all passed on 2026-04-02.
- Next best action: Check whether queue hygiene needs a filter for tool-call traffic in tool-enabled stages.

## Update Stamp
- Last updated: 2026-04-02
- Owner: Codex
