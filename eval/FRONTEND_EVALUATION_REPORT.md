# PathFinder Frontend Evaluation Report

Date: 2026-04-11

## Scope

This run focused on local frontend evaluation using the dev debug harness:

- General fixture sweep across Profile, Stage, Test, Chat, Debug, escalation lock, and long-text states.
- Forced-stage and forced-stage-finish behavior.
- Stage completion changes as reflected in the ProgressBar and Stage tab.
- Profile tab readability during forced and completed stage states.
- Desktop and mobile overflow checks.

The canonical workflow was added in the vault:

`D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\evaluation\frontend_evaluation_how_to_use.md`

## Environment

- Backend: `http://localhost:8000`, started with `PATHFINDER_DEBUG=1`
- Frontend: `http://localhost:3000`
- Browser tool: `agent-browser 0.25.3`
- Desktop viewport: `1280x720`
- Mobile viewport: `390x844`

## Fixes Made

1. Exposed scripted forced-stage helpers on `window.__PF_DEBUG__`.
   - `forceStage(stage, options)`
   - `finishForcedStage(stage, options)`

2. Changed Debug tab fixture buttons to apply frontend-only state by default.
   - This keeps local feature testing usable even when the backend is down.
   - Trace buttons still require the backend.

3. Fixed forced-stage ProgressBar behavior.
   - Forced mode now keeps the real current stage visible.
   - Example: current `thinking` plus forced `job` marks both `thinking` and `job` active.
   - Normal completed current stages now stay complete; `finish uni` no longer leaves `uni` active.

4. Fixed Stage tab forced-stage behavior.
   - In forced mode, the anchor stage is the active Stage card.
   - Other stages remain pending unless they are explicitly completed.

5. Added non-visual status attributes for browser assertions.
   - Progress markers: `data-progress-stage`, `data-progress-state`
   - Stage cards: `data-stage-card`, `data-stage-status`

## Edge-Case Matrix

Force cases:

| Case | ProgressBar | Stage Tab | Result |
|---|---|---|---|
| force thinking | thinking active | thinking active | Pass |
| force purpose | thinking active, purpose active | purpose active | Pass |
| force goals | thinking active, goals active | goals active | Pass |
| force job | thinking active, job active | job active | Pass |
| force major | thinking active, major active | major active | Pass |
| force uni | thinking active, uni active | uni active | Pass |

Finish cases:

| Case | ProgressBar | Stage Tab | Result |
|---|---|---|---|
| finish thinking | thinking complete, purpose active | thinking complete, purpose active | Pass |
| finish purpose | thinking/purpose complete, goals active | thinking/purpose complete, goals active | Pass |
| finish goals | thinking/purpose/goals complete, job active | thinking/purpose/goals complete, job active | Pass |
| finish job | thinking through job complete, major active | thinking through job complete, major active | Pass |
| finish major | thinking through major complete, uni active | thinking through major complete, uni active | Pass |
| finish uni | all stages complete | all stages complete | Pass |

No force or finish case produced an error overlay or horizontal overflow.

## Browser Evidence

Screenshots:

- `eval/frontend-eval/2026-04-11/force-job-profile-progress.png`
  - Shows current `thinking` and forced `job` both active in the ProgressBar.
- `eval/frontend-eval/2026-04-11/force-job-stage.png`
  - Shows Stage tab focused on forced `job`.
- `eval/frontend-eval/2026-04-11/finish-job-stage.png`
  - Shows stages through `job` complete and `major` active.
- `eval/frontend-eval/2026-04-11/finish-uni-stage.png`
  - Shows final-stage completion edge case with all progress markers complete.
- `eval/frontend-eval/2026-04-11/force-major-profile.png`
  - Profile tab under forced future-stage state.
- `eval/frontend-eval/2026-04-11/force-major-stage-fixed.png`
  - Stage tab after fixing forced-stage active-card mismatch.
- `eval/frontend-eval/2026-04-11/mobile-long-text.png`
  - Mobile long-text state with no horizontal overflow.

Representative browser assertions:

```text
force job progress:
thinking=active, purpose=pending, goals=pending, job=active, major=pending, uni=pending

force job Stage tab:
thinking=pending, job=active, purpose=pending, goals=pending, major=pending, uni=pending

finish uni progress:
thinking=complete, purpose=complete, goals=complete, job=complete, major=complete, uni=complete

finish uni Stage tab:
thinking=complete, job=complete, purpose=complete, goals=complete, major=complete, uni=complete
```

## Fixture Sweep

Fixtures checked with `window.__PF_DEBUG__.applyFixture(name, { backend: false })`:

- `empty`
- `quizSeeded`
- `activeThinking`
- `activePurpose`
- `activeGoals`
- `activeJob`
- `activeMajor`
- `activeUni`
- `allComplete`
- `pathDebateReady`
- `userTagAlerts`
- `escalationLock`
- `longText`

Result: all passed with no error overlay and no horizontal overflow.

## Verification

Commands passed:

```powershell
cd frontend
npm run lint
npm run build
```

```powershell
venv\Scripts\python -m unittest test_main_contract.py test_debug_trace_contract.py
```

Browser checks passed:

- Page loads at `http://localhost:3000`
- `window.__PF_DEBUG__` is present in Vite dev mode
- No Vite/Next error overlay detected
- Desktop fixture and forced-stage sweeps have no horizontal overflow
- Mobile long-text fixture has no horizontal overflow

## Residual Risk

- This was a local dev harness pass, not a full production build browser replay.
- The forced-stage fixtures intentionally simulate state; they do not prove the backend graph will always emit the exact same state sequence.
- The Stage tab is taller than the desktop viewport for some states; `agent-browser scrollintoview` is needed for lower cards and Debug tab lower buttons.
- Vietnamese text appears readable in the browser screenshots, but some source files still display mojibake in terminal output. This report did not address text encoding cleanup.
