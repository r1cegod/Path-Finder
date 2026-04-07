# Context Maintenance

> ARCHIVED REPO COPY. The live canonical version of this file now lives at:
> `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\context\how to\context_maintenance.md`
>
> The repo `docs/` folder is archive-only and should not be treated as the source of truth.

## File Roles
- `docs/context/docs/PROJECT_CONTEXT.md`: stable repo facts that should survive session compaction.
- `docs/context/docs/CURRENT_CONTEXT.md`: live working notes, blockers, and handoff details for the current cycle.
- `D:\ANHDUC\Path_finder\logs\DEV_LOG.md`: repo mirror of the append-only engineering decision history.

## Update Rules
1. Put stable architecture facts in `PROJECT_CONTEXT.md`.
2. Put active tasks, blockers, and "what to do next" in `CURRENT_CONTEXT.md`.
3. When a decision should survive beyond the current work cycle, also record it in `D:\ANHDUC\Path_finder\logs\DEV_LOG.md`.
4. Link to source docs instead of copying large prompt or architecture sections.
5. Prefer `docs/...` paths over legacy root docs that are being removed.
6. Update dates when a stable fact changes.

## Good Candidates For PROJECT_CONTEXT.md
- Stage order
- Core architecture shape
- Stable code conventions
- Canonical doc locations
- Repeated verification commands

## Good Candidates For CURRENT_CONTEXT.md
- Current objective
- Files being edited
- Open risks
- Test commands for this work
- Best next step for the next session

## Avoid
- Long copied prompt text
- Per-turn troubleshooting logs
- Facts that are already obsolete or under active debate
