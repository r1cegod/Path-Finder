# PathFinder Uncertainty Attack Report - 2026-04-12

Status: paused before chat; pre-chat test-path bugs fixed

## Mission

Attack with uncertainty.

This run tests a normal student who does not have a stable view yet. The goal is not to reward crisp self-authored answers. The goal is to see whether PathFinder can work with real indecision without soft-locking, over-drilling, prematurely deciding, or treating confusion as bad faith.

## Production Target

PathFinder should help an uncertain but cooperative student move from vague preference to usable direction.

Success means:

- The system distinguishes genuine uncertainty from avoidance, compliance, or trolling.
- The system asks concrete tradeoff questions instead of requiring the student to already know their path.
- The system does not punish "I don't know" when it is honest.
- The system extracts weak but usable signals from normal answers.
- The system does not claim a stage is complete unless raw backend state agrees.
- The run can reach at least Thinking and Purpose completion, and ideally Goals handoff, without forcing a fake confident persona.

Failure means:

- The student gets trapped in repeated probes after giving reasonable uncertain answers.
- The system escalates, scolds, or over-reality-checks normal confusion.
- The assistant states stage progress that raw state does not support.
- The frontend/backend crashes.
- The system requires the student to invent a precise goal too early.

## Human Profile

Name: Linh

Baseline:

- Grade 12 student in Vietnam.
- Cooperative and sincere, but not self-authored yet.
- Does not know whether to choose Business, IT, Marketing, Psychology, or Design.
- Parents prefer a stable major with job security.
- Student cares about salary and employability, but also wants something not boring.
- Has tried small activities but no deep portfolio.
- English is decent, math is average, coding exposure is shallow.
- Answers should be normal, mixed, and sometimes uncertain.

Behavior rules:

- Do not act as a student who already knows product/UX or any final path.
- Give honest partial answers.
- Use "em không chắc", "chắc là", "em sợ chọn sai", and mixed preferences.
- When forced to choose, choose reluctantly and explain the tradeoff.
- Do not troll or refuse the process.

## Run Protocol

1. Start backend with `PATHFINDER_DEBUG=1`.
2. Start frontend at `http://localhost:3000`.
3. Verify page load and no error overlay.
4. Create a fresh session using `window.__PF_DEBUG__.newSession()`.
5. Start trace using `window.__PF_DEBUG__.startTrace()`.
6. Submit both tests through the frontend UI.
7. Chat as Linh until one of these happens:
   - `rawState.goals?.done === true`
   - a hard runtime error occurs
   - a soft lock is observed for 5+ turns
   - escalation triggers incorrectly
8. Every turn: record only the latest assistant response summary and raw state summary.
9. Every 5 turns: check Profile and Stage tabs for overlay, overflow, and stage-card status.
10. Stop trace and record trace session ID.

## Completion Verification

Do not accept assistant wording as completion.

Raw-state checks:

```javascript
const payload = await window.__PF_DEBUG__.getBackendState()
JSON.stringify({
  currentStage: payload.frontendState.currentStage,
  completedStages: payload.frontendState.completedStages,
  thinkingDone: payload.rawState.thinking?.done,
  purposeDone: payload.rawState.purpose?.done,
  goalsDone: payload.rawState.goals?.done,
  escalationPending: payload.rawState.escalation_pending,
})
```

## Turn Log

| Turn | User stance | Assistant behavior | Raw stage state | Finding |
|---:|---|---|---|---|
| 0 | Planned uncertainty profile | Not started | Fresh debug session created | Report scaffold created before run |
| Test | Normal mixed RIASEC answers | N/A | `riasec_top` submitted | Pass |
| Test | Mixed Brain Test with no MI category >= 80% | N/A | `brain_type: []` | Found completion bug; fixed |

## 5-Turn Checkpoints

| Turn | Profile tab | Stage tab | Overlay | Horizontal overflow | Notes |
|---:|---|---|---|---|---|
| 5 | Pending | Pending | Pending | Pending | Pending |
| 10 | Pending | Pending | Pending | Pending | Pending |
| 15 | Pending | Pending | Pending | Pending | Pending |
| 20 | Pending | Pending | Pending | Pending | Pending |

## Findings

1. Empty-dominant Brain Test result soft-locked the Test tab.
   - Normal uncertain profile produced no MI category above the 80% threshold.
   - Backend received `brain_type: []`.
   - Frontend used `brain_type.length > 0` as the only completion signal, so the Brain Test card stayed ready instead of completed.
   - This is a normal-student bug, not an edge case: uncertain or balanced students can produce no dominant MI type.

2. Test completion status overwrote previous completion state.
   - After RIASEC submit, frontend state had `riasecSubmitted: true`.
   - After Brain Test submit, backend response included `riasecSubmitted: false` because that request was not a RIASEC submission.
   - Frontend shallow merge replaced the previous true flag with false.
   - Cards still completed when `riasec_top` was non-empty, but the status object was wrong and would fail for any future completion logic that relies on `testStatus`.

3. Full uncertainty chat run is intentionally deferred.
   - User paused the session before chat and asked to finish the bugs first.
   - Next run should start from a fresh session with the same Linh profile.

## Fixes Made

- Backend `/test/{session_id}` now treats provided empty lists as real submissions by checking `request.model_fields_set`.
- Backend streams `testStatus` with each test response.
- Frontend `DEFAULT_APP_STATE` now includes `testStatus`.
- Frontend Test tab completion now accepts either real result values or `testStatus`.
- Frontend state merge now keeps test completion booleans sticky once true.

## Evidence

- Empty Brain Test verification produced `brain_type: []`.
- Both Test cards rendered as `HOÀN THÀNH` after the fix path.
- Verified:

```powershell
npm run lint
npm run build
venv\Scripts\python -m unittest test_debug_trace_contract.py test_stage_profile_utils_contract.py test_main_contract.py
```

## Residual Risk

- Need a fresh uncertainty chat run after the test-path bugs are fixed.
- Need to verify whether PathFinder can advance uncertain student answers through Thinking, Purpose, and Goals without over-drilling or premature stage claims.
