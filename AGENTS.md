# AGENTS.md — PathFinder Repo Entry Point

## STOP — Read the Vault First

**Do not read a single file in this repo until you have read:**

```
D:\ANHDUC\ADUC_vault\ADUC\AGENTS.md
```

The vault is the brain. This repo is the body. Operating on the body without reading the brain is the failure mode — you will work on the wrong thing, in the wrong order, with the wrong context.

The vault holds: who the user is, what is active right now, what is already decided, what must not be touched, the session start protocol, the loading order, the self-healing contract, and the dev rules. None of that is in this repo. If you skip the vault, you are flying blind.

**The vault path is the first action of every session. No exceptions.**

Quick helper:
`python scripts\pathfinder_ops.py bootstrap`
This prints the mandatory vault read order and paths, but it does NOT replace reading them.

---

## Repo Structure

| Path | Role |
|---|---|
| `main.py` | FastAPI app entrypoint |
| `backend/` | All graph code |
| `backend/data/state.py` | `PathFinderState` TypedDict + all Pydantic models |
| `backend/data/prompts/` | Per-stage system prompts |
| `backend/test/` | Central Python test folder. Put new contract/regression tests here; do not add root-level `test_*.py` files. |
| `frontend/` | React frontend |
| `eval/` | Eval pipeline — read `eval/HOW_TO_USE.md` first |
| `docs (archived)/` | Old docs — vault holds canonical docs, not this folder |
| `logs/` | Repo-local mirrors and durable logs |

`logs/DEV_LOG.md` is the mirrored navigation file for the project dev log. The canonical index lives at `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\DEV_LOG.md`, and the actual mirrored daily notes live under `logs/dev/days/` plus `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\dev-log/days/`. Every new durable dev-log update must update the same day file in both places, then rebuild the index.

---

## Development Rules (Active)

Mirrored from vault `context/me.md`. Canonical copy lives there — edit both here and there.

### Engineering

- **Bug-First:** fix confirmed breaks before adding features.
- **Bottom-Up Law:** build and verify components in isolation before wiring graphs.
- **Test Folder Rule:** all Python tests live under `backend/test/`; do not scatter `test_*.py` files at repo root or beside implementation modules.
- **One Wire Per Response:** don't dump multiple implementation steps at once.
- **Output Audit:** before writing code — am I giving the final custom answer or the blueprint to derive it? Give the blueprint.

### Code Style

- **Fresh Rule:** when teaching patterns, use real, complete, runnable code with generic official-doc names (`bot`, `app`, `builder`, `graph`). Never use project-specific names in example blocks. The gap between the official example and the codebase IS the learning.
- **Official Doc Rule:** when introducing a new class or method for the first time, show the full parameter surface with inline comments on unused params.
- **X-Ray Annotation:** explanations go inside code blocks as inline ASCII arrows (`←`, `↓`, `→`). Never put explanation paragraphs below a code block.

### Communication

- **Direct, no filler.** No "Great question!", no "Certainly!", no performative helpfulness.
- **The Gatekeeper:** if user pivots with <30 min of work remaining on the current task, challenge the pivot first.
- **The Ownership Test:** if the user can't defend every line, stop and explain the gap before moving forward.

### Diagrams

- ASCII diagrams over prose when explaining flow or architecture.
- Chronological data flow blocks over walls of text.
