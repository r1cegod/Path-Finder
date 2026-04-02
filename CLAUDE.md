# PathFinder — Project Context

## What This Is
AI career/university counselor for Vietnamese students. LangGraph multi-agent backend (Python 3.13, Pydantic v2, gpt-4o-mini). FPT SE Scholarship portfolio piece.

## Context Sources (read these, not this file)
@docs/context/docs/PROJECT_CONTEXT.md
@docs/context/docs/CURRENT_CONTEXT.md
@docs/architecture/docs/ARCHITECTURE.md
@docs/architecture/docs/state_architecture.md

## Auto-Update Rule
When something changes, write it to the right doc — never into this file:
- **Live work / blockers / handoff** → `docs/context/docs/CURRENT_CONTEXT.md`
- **Durable decisions / locked facts** → `docs/context/docs/PROJECT_CONTEXT.md`
- **Architecture change / new ADR** → `docs/architecture/docs/ARCHITECTURE.md`
- **State field change** → `docs/architecture/docs/state_architecture.md`
- **End-of-session summary** → `docs/DEV_LOG.md`

## Code Conventions
- **Black** 100 chars, **Ruff** linting, **Pylance** basic type checking
- All Pydantic models in `backend/data/state.py` — no separate models file
- `FieldEntry(BaseModel)`: `{content: str, confidence: float}` wraps every extractable field
- `ConfigDict(extra="forbid")` on all structured output classes
- `model_copy(update={...})` for Pydantic updates
- Absolute imports: `from backend.data.state import ...`
- Prompts are f-string templates in `backend/data/prompts/{stage}.py`
- Agent responses in **Vietnamese**. Code/comments/docs in **English**.
- `load_dotenv()` MUST run before any `ChatOpenAI` instantiation
- New state fields need a writer, a reader, and an exit condition

## Test Commands
- Terminal test: `python test.py`
- LangGraph Studio: `langgraph dev`
- Import check: `python -c "from backend.orchestrator_graph import input_orchestrator; print('OK')"`
