# Current Context

> ARCHIVED REPO COPY. The live canonical version of this file now lives at:
> `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\context\docs\CURRENT_CONTEXT.md`
>
> The repo `docs/` folder is archive-only and should not be treated as the source of truth.

Use this file as the short-lived working scratchpad for the current build cycle.
Move durable decisions to `PROJECT_CONTEXT.md` or `D:\ANHDUC\Path_finder\logs\DEV_LOG.md`.

## Active Goal
- Goal: Tighten the official evaluation pipeline with a 3-round production gate.
- Success condition: the official evaluation doc requires a plan capped at 3 rounds, one finished stage per run, log handoff after each run, and user conversation before the next round.
- Deadline or milestone: 2026-04-06 evaluation-pipeline gate update.

## Current Workstream
- Area: Repo instruction and navigation alignment after establishing the mirrored PathFinder vault workspace.
- Files in play: `AGENTS.md`, `docs/context/docs/PROJECT_CONTEXT.md`, `docs/context/docs/CURRENT_CONTEXT.md`, `D:\ANHDUC\Path_finder\logs\DEV_LOG.md`
- Why this matters now: the vault is now a real project-routing layer, so the repo instructions need to state the repo-vs-vault boundary explicitly instead of relying on chat history.

## Open Questions
- Question: Should repo instruction updates also require a mirrored vault re-ingest policy, or is router-level maintenance enough for now?
- Blocking component: none for the doc update itself.
- Next check: validate the new repo-plus-vault read path in the next real coding session.

## Risks And Constraints
- Risk: agents may treat the vault as canonical if the boundary is not stated explicitly inside the repo.
- Evidence: the vault now has strong summaries and hubs, which makes it easy to over-trust if the contract is not documented.
- Mitigation: repo instructions now define the vault as a routing layer only, with `docs/` remaining canonical.

## Commands To Re-Run
- `python eval/run_eval.py --mode multi --file eval/<target_attack>.jsonl --graph <target_graph>`
- `python eval/run_eval.py --mode single --file eval/<target_attack>.jsonl --graph <target_graph>`

## Handoff
- Latest change: updated repo instruction docs so agents can use the mirrored Obsidian PathFinder workspace as a low-token routing layer while still treating repo `docs/` as the source of truth.
- Verification completed:
  - manual doc inspection of `AGENTS.md`
  - manual doc inspection of `docs/context/docs/PROJECT_CONTEXT.md`
  - manual doc inspection of `docs/context/docs/CURRENT_CONTEXT.md`
- Next best action: test the new repo-plus-vault navigation flow during the next real implementation task and refine it only if it creates ambiguity.

## Update Stamp
- Last updated: 2026-04-06
- Owner: Codex
