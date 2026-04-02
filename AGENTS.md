# Repository Guidelines

## Context First
Start each non-trivial task by reading the docs that hold repo context before changing code.
- Stable repo facts: `docs/context/docs/PROJECT_CONTEXT.md`
- Live work, blockers, and handoff: `docs/context/docs/CURRENT_CONTEXT.md`
- Context maintenance rules: `docs/context/how to/context_maintenance.md`
- Architecture source of truth: `docs/architecture/docs/ARCHITECTURE.md`
- State contract: `docs/architecture/docs/state_architecture.md`
- Stage prompt docs: `docs/prompt/docs/stage_prompt.md`
- Output prompt docs: `docs/prompt/docs/output_prompt_architecture.md`
- Prompt implementation guide: `docs/prompt/how to/production_system_prompts.md`
- Evaluation history: `docs/evaluation/stage_evaluation.md`
- Durable decision history: `docs/DEV_LOG.md`

Prefer `docs/...` paths over legacy root docs. When a doc has both `docs/` and `how to/`, use `docs/` for source-of-truth facts and `how to/` for maintenance workflow.

## Project Structure & Module Organization
`backend/` contains the LangGraph application: `orchestrator_graph.py`, `output_graph.py`, one `*_graph.py` per stage, and shared state in `backend/data/state.py`. Prompt templates live in `backend/data/prompts/`. `main.py` exposes the FastAPI streaming API. `frontend/` is the Vite app, with UI code in `frontend/src/` and API helpers in `frontend/src/api/`. Evaluation assets and attack datasets live in `eval/`. Documentation is organized under `docs/architecture/`, `docs/prompt/`, `docs/evaluation/`, and `docs/context/`, with canonical docs in each `docs/` subfolder.

## Build, Test, and Development Commands
- `venv\\Scripts\\activate` to enter the local Python environment on Windows.
- `python main.py` starts the backend entrypoint for local API work.
- `uvicorn main:app --reload` is the fastest backend dev loop when changing API code.
- `python test.py` runs the current smoke test against the orchestrator graph.
- `langgraph dev` runs the graph in LangGraph Studio for node-level inspection.
- `cd frontend && npm run dev` starts the Vite UI on port 3000.
- `cd frontend && npm run build` creates a production frontend build.
- `cd frontend && npm run lint` runs TypeScript checks (`tsc --noEmit`).

## Critical Development Rules
- Python owns routing, counters, thresholds, and state transitions. LLMs classify and synthesize, but they do not own control flow.
- Path is not a stage agent. It is handled in Output Compiler Case B2 after all 6 profiles are `done=True`.
- The output compiler is the only student-facing response generator.
- All Pydantic state and profile models live in `backend/data/state.py`.
- New state fields need a writer, a reader, and an exit condition. Update `docs/architecture/docs/state_architecture.md` when the contract changes.
- `load_dotenv()` must run before any OpenAI or `ChatOpenAI` client initialization.
- Student-facing responses stay in Vietnamese. Code, comments, and docs stay in English.
- Keep one source of truth per concept. If a canonical doc exists in `docs/`, update it instead of duplicating long instructions elsewhere.
- User ALWAYS need to learn what they need to use multiple time in the future, skip one time feature learning (only understanding)

## Coding Style & Naming Conventions
Use 4-space indentation in Python. Follow the repo convention documented in `CLAUDE.md`: Black-style formatting (100-char lines), Ruff-style linting, and absolute imports such as `from backend.data.state import PathFinderState`. Keep Pydantic models in `backend/data/state.py`. Name stage files consistently (`thinking_graph.py`, `purpose_graph.py`, `uni_graph.py`). Prompt modules use uppercase constant names like `PURPOSE_DRILL_PROMPT`.

## Testing Guidelines
This repo currently relies on smoke tests and eval datasets rather than a full pytest suite. Add focused Python tests as `test_<feature>.py` at the repo root when introducing routing or state logic. For behavioral changes, update or add datasets in `eval/*.jsonl` and record the scenario in `docs/evaluation/stage_evaluation.md`. Run `python test.py` before submitting backend changes.

## Context Maintenance & Auto Update
Treat context maintenance as part of done, not optional follow-up.
- Update `docs/context/docs/CURRENT_CONTEXT.md` when the active goal, files in play, blockers, rerun commands, or handoff notes change.
- Update `docs/context/docs/PROJECT_CONTEXT.md` when stable architecture facts, canonical doc locations, or repo-wide conventions change.
- Append `docs/DEV_LOG.md` when a decision should survive beyond the current work cycle.
- If you change architecture, state shape, prompt structure, or evaluation strategy, update the matching docs in `docs/` in the same change.
- Link to canonical docs instead of copying large sections into scratch files.
- Do not leave `CURRENT_CONTEXT.md`, `PROJECT_CONTEXT.md`, or related source-of-truth docs stale after substantial work.

## Commit & Pull Request Guidelines
Recent commits use short, direct subjects such as `Frontend update`, `MVP-done`, and `orchestrator now manage stage`. Keep commit titles brief, imperative, and scoped to one change; avoid vague messages like `again`. PRs should state the purpose, list touched areas (`backend/`, `frontend/`, `docs/`), mention test commands run, and include screenshots for UI changes or sample request/response notes for API changes.

## Security & Configuration Tips
Do not commit `.env`, `.langgraph_api/`, `venv/`, or local trace artifacts. `load_dotenv()` must run before creating OpenAI clients. Keep student-facing responses in Vietnamese, but keep code, comments, and docs in English.
