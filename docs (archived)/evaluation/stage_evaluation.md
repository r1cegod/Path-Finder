# Stage Evaluation: Attack Protocol Log

Reference:
- Official evaluation pipeline and runner workflow: `eval/HOW_TO_USE.md`
- For web-enabled `job` / `major` / `uni` stage methodology, use `docs/evaluation/data_agent_evaluation.md`.
- For the current Stage 0 deep audit, use `docs/evaluation/thinking_evaluation.md`.
- For the current Stage 1 deep audit, use `docs/evaluation/purpose_evaluation.md`.
- For the current Stage 2 deep audit, use `docs/evaluation/goals_evaluation.md`.
- For retrieval-stage notes, use `docs/evaluation/job_evaluation.md`.

## 1. Macro Architecture
This file tracks the evaluation seam for the knowledge-stage agents.

Pipeline for a stage:
`Input Parser` -> `Target Extractor (Confident Node)` -> `Target Analyst (Drill Node)` -> `Output Compiler`

## 2. Stage 0: Thinking Agent
Canonical Stage 0 audit log: `docs/evaluation/thinking_evaluation.md`

## 3. Stage 1+: Pointers
- **Purpose:** canonical audit log is `docs/evaluation/purpose_evaluation.md`.
- **Goals:** canonical audit log is `docs/evaluation/goals_evaluation.md`.
- **Job:** retrieval-evaluation notes are in `docs/evaluation/job_evaluation.md`.

## 4. Open Gap
Stage 0 now has both:
- deterministic trailing `PROBE:` composition in Python, and
- a graph-level single-turn confidence clamp that prevents false Stage 0 lock-in.

The next meaningful escalation is orchestrator/output end-to-end evaluation that verifies the stronger Stage 0 handoff survives the full pipeline. A longer multi-turn contradiction dataset for Thinking is still valuable, but it is now secondary to end-to-end replay.
