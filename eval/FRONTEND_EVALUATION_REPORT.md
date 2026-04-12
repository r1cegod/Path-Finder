# PathFinder Frontend Evaluation Report

## Current Focused Live Reports

- 2026-04-12 frontend trace output regression: `eval/live_frontend_output_regression_2026-04-12.jsonl`
- 2026-04-12 uncertainty attack: `eval/UNCERTAINTY_ATTACK_REPORT_2026-04-12.md`
- 2026-04-12 real-Duc identity continuation: `eval/IDENTITY_CONTINUATION_GOALS_REPORT_2026-04-12.md`

### 2026-04-12 Frontend Trace Output Regression

Source traces:

- `eval/threads/f942d643-8941-40f7-ab6d-d378e0e6fe7f/traces/live_0019.json`
- `eval/threads/f942d643-8941-40f7-ab6d-d378e0e6fe7f/traces/live_0020.json`
- `eval/threads/f942d643-8941-40f7-ab6d-d378e0e6fe7f/traces/live_0021.json`
- `eval/threads/duc-goals-continuation-20260412/traces/live_0004.json`

The first three rows reproduce the frontend finding where Purpose had strong evidence but `purpose.done === false`, while the output compiler still drifted into Goals/Job/Major wording. The fourth row keeps the old documented Goals transition-lag state as a comparison case; the current graph now has a `post_stage_manager` fix for fresh same-turn completions.

Fix:

- Output stage progress now distinguishes `stage marked complete` from `all fields filled, but stage is not marked complete`.
- Incomplete current stages inject `<current_stage_lock>`, suppress future-stage pivot offers, and append a final runtime override after the conversation messages so raw backend state wins over the latest user topic.
- Follow-up integration check narrowed `<current_stage_lock>` so it no longer conflicts with the upgraded `STAGE_INTRO_BLOCK`: transition turns may acknowledge the previous-stage handoff, but cannot move beyond the newly active current stage.
- Stage prompt audit found Purpose lacked the Goals-style handoff-sufficiency policy. `purpose.py` now defines Purpose as an identity-prior checkpoint and lets risk/core/location fields become handoff-stable when execution realism belongs to Goals, Job, or Major.
- Sub-orchestrator workers now read a 2.5k-token recent tail while the 5k `routing_memory` lane remains available for summarization, reducing every-fifth-turn fanout cost without dropping the long-memory summaries.

Verification:

```powershell
venv\Scripts\python eval\run_eval.py --mode multi --file eval\live_frontend_output_regression_2026-04-12.jsonl --graph output --workers 1
venv\Scripts\python -m unittest test_output_prompt_contract.py test_output_graph_contract.py test_orchestrator_graph_contract.py test_purpose_prompt_contract.py test_sub_orchestrator_graph_contract.py test_stage_profile_utils_contract.py test_message_window_contract.py test_main_contract.py test_debug_trace_contract.py
```

Final semantic audit:

- All 4 output rows ran successfully.
- The three incomplete-Purpose rows stayed inside Purpose and did not ask Goals/Job/Major handoff questions.
- The old Goals transition-lag row remained usable as a documented regression case; the current graph has a post-stage manager fix that still needs a fresh live run.
- Latest rerun after the stage-intro/output-lock integration check passed 4/4 rows and 56 focused contracts.

### 2026-04-12 Real-Duc Identity Continuation

The previous real-Duc trace was restored from `live_0051.json` into debug session `duc-goals-continuation-20260412` instead of replaying 51 turns.

Result:

- Goals completed.
- Session advanced to `currentStage: "job"`.
- Final Goals profile is stable on: `$10k/month`, full autonomy, solo-first/small team, AI-agent client-work path, paid pilot deliverable, and portfolio-first credential strategy.

Runtime findings:

- Stage transition originally had a one-turn lag: the turn that first set `goals.done === true` still responded as Goals because `stage_manager` ran before same-turn extraction.
- Follow-up fix: `post_stage_manager` now runs after each stage graph and before `context_compiler`, so same-turn completion can advance the active stage before the response prompt is built.
- PowerShell here-string input corrupted Vietnamese accents in saved trace `input.message`; future runs should use `eval/live_session_probe.py send --message-file <utf8-file>`.

Workflow change:

- Added `eval/live_session_probe.py` for restore/start/send/state/stop loops with compact state output.
- Identity-continuation prompt evaluation should use raw `output` restore plus compact state checks when the frontend UI is not the test target.

### 2026-04-12 Uncertainty Attack Pre-Chat Bugs

Before the uncertainty chat started, the normal mixed student profile exposed two Test tab bugs:

- Brain Test submissions with no MI category above 80% produced `brain_type: []` and did not mark the card complete.
- `testStatus` used a shallow merge, so submitting one test could overwrite the previous test's completion flag back to false.

Both were fixed and verified with frontend lint/build plus backend contract tests.

## 2026-04-12 Live User-Like Frontend Run

### Scope

This run used the real frontend and backend in debug mode to behave like a student:

- Created a mock student profile: grade-12 Vietnamese student, product/UX leaning, wants near-user product work, uses AI as leverage, wants international/remote-hybrid options.
- Took both frontend tests through the UI path.
- Chatted from Thinking through Purpose and into the first Goals turn.
- Checked only the latest assistant reply after each turn.
- Checked Profile and Stage tabs at turns 5, 10, 15, and 20.
- Stopped when hard runtime blockers made the run no longer a clean Goals completion proof.

### Environment

- Backend: `http://127.0.0.1:8000`, debug mode enabled.
- Frontend: `http://localhost:3000`.
- Main trace session: `f942d643-8941-40f7-ab6d-d378e0e6fe7f`.
- Trace evidence: `eval/threads/f942d643-8941-40f7-ab6d-d378e0e6fe7f/traces/live_0001.json` through `live_0024.json`.
- Follow-up clean quiz session after patches: `7dbcdfef-991f-41bb-9865-aba6620f822c`.

### Findings

1. **Hard backend error after quiz submission.**
   - Trigger: submit both RIASEC and Brain Test, then send the first chat message.
   - Error: `ThinkingProfile` validation failed because `/test/{session_id}` wrote only `riasec_top` and `brain_type`, leaving required Thinking fields missing.
   - Fix: `/test/{session_id}` now seeds a valid incomplete `ThinkingProfile` with low-confidence `not yet` fields before merging quiz results.
   - Regression: `test_test_endpoint_merges_mi_and_riasec_for_same_session`.

2. **Hard backend error entering Goals.**
   - Trigger: after Purpose completed, the first Goals extraction returned nested `goals.long` and `goals.short` objects without their `done` fields.
   - Error trace: `eval/threads/f942d643-8941-40f7-ab6d-d378e0e6fe7f/traces/live_0024.json`.
   - Fix: `GoalsLongProfile.done` and `GoalsShortProfile.done` now default to `False`; Python normalization recomputes the actual nested and wrapper done flags.
   - Regression: `test_goals_nested_profiles_tolerate_missing_done_from_structured_output`.

3. **User-facing stage language drifted ahead of raw state.**
   - At turns 20-21, the assistant said Goals was locked and Job/Major was next.
   - Raw backend state still had `goals: null`, `job: null`, and `purpose.done: false`.
   - Runtime flaw: completion must be verified from raw `getBackendState()` stage data, not assistant wording.

4. **Purpose repeated the same risk tradeoff too many times.**
   - The user gave several direct answers about accepting lower certainty for near-user product/UX work.
   - Purpose continued to re-ask variants of the same safety/risk question until turn 23.
   - This eventually completed Purpose, but it is a product-quality flaw and token-cost risk.

5. **Long browser automation scripts can destabilize the local browser daemon on this Windows machine.**
   - After large inline `agent-browser eval` helpers and a 24-turn trace, PowerShell hit a paging-file error and the browser daemon later stopped responding.
   - The optimized workflow now recommends smaller reusable snippets and periodic tab checks instead of oversized one-off scripts.

### Checks

- Profile tab checkpoints: turns 5, 10, 15, and 20 had no error overlay and no horizontal overflow.
- Stage tab checkpoints: turns 5, 10, 15, and 20 had no error overlay and no horizontal overflow.
- Static/focused backend checks passed after fixes:

```powershell
venv\Scripts\python -m unittest test_stage_profile_utils_contract.py test_debug_trace_contract.py test_main_contract.py
```

### Workflow Update

The canonical frontend workflow was updated:

`D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\evaluation\frontend_evaluation_how_to_use.md`

New live-run rules:

- Batch-click quiz buttons with `agent-browser eval`.
- Check only latest assistant response plus state each turn.
- Check Profile and Stage tabs every 5 turns.
- Verify stage completion from `window.__PF_DEBUG__.getBackendState()`, not from assistant text.

### Residual Risk

- A full clean run to `goals.done === true` was not completed after the second fix because the browser automation session became unstable.
- The latest backend patches have focused unit coverage but still need one fresh end-to-end live run from tests to Goals completion.
- The trace session `f942d643-8941-40f7-ab6d-d378e0e6fe7f` was interrupted by backend restarts, so its `live_session.json` still shows active even though the process was restarted.

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
