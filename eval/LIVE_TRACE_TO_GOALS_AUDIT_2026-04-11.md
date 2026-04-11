# Live Trace To Goals Audit - 2026-04-11

Source trace:
`eval/threads/13265a9e-63c7-45d8-9fdc-903fe5774547/`

## Scope

This is a full-product live trace audit, not a stage-local replay signoff.
The run started at Thinking and stopped at Goals:

- Trace count: 51 live turns
- Trace window: 2026-04-11 14:08 to 15:38 +07:00
- Token total: 999,745 logged tokens
- Final stage: `goals`
- Completed profiles by final trace: `thinking`, `purpose`
- Incomplete profile by final trace: `goals.done=false`

## Stage Timeline

| Turn | Stage after turn | Result |
| --- | --- | --- |
| 1-10 | thinking | Thinking profile fills, but stays in stage. |
| 11 | purpose | Thinking transitions to done. |
| 12-22 | purpose | Purpose profile fills, but stays in stage. |
| 23 | goals | Purpose transitions to done. |
| 24-51 | goals | Goals keeps drilling and does not complete. |

## Confirmed Issues

### 1. Streamed output was not sanitized

`output_graph` sanitized the final AIMessage, but `main.py` streamed raw `output_compiler`
chunks before that sanitized state existed. The final state was clean, while
`assistant_text` and the live UI stream could contain non-Latin foreign-script tokens.

Observed in live traces:

- `live_0024.json`
- `live_0031.json`
- `live_0039.json`

Patch applied:

- Added shared student text safety helpers in `backend/text_safety.py`.
- Kept final message sanitization in `backend/output_graph.py`.
- Sanitized streamed `output_compiler` tokens in `main.py` before sending SSE data or
  writing `assistant_text` into the live trace.

### 2. Goals did not close after enough evidence

By turn 51, Goals had extracted all seven fields with non-empty content, but confidence
remained capped at `0.4-0.6`, so downstream done counting correctly kept
`goals.done=false`.

This is not a Python exit bug. It is a product behavior question:

- Current rule: only `confidence > 0.8` can count as done.
- Live behavior: Goals keeps asking for deeper proof around first-client validation,
  contract pricing, and first-dive audit strength.
- Risk: the counselor can become too hard to satisfy for a self-authored student who is
  already giving a concrete but early-stage plan.

Decision needed before patching:

- Keep Goals strict and require stronger execution proof before completion.
- Or add a "planning-ready but not proof-ready" completion mode so the system can move
  forward while marking low-confidence execution assumptions for Job/Major.

### 3. Token cost spikes during late Goals

Eight turns crossed 30k tokens. The largest was turn 51 at 56,612 tokens.
The cost was not from `output_compiler`; it came mostly from user-tag fanout,
`confident`, and `goals_agent` as context grew.

Spike turns:

- Purpose: 16, 21
- Goals: 26, 31, 36, 41, 46, 51

This supports a follow-up deterministic or low-cost check around what context each
tagger needs during long full-product sessions.

## Strong Replay Candidates

### Candidate A - Stream sanitizer regression

Purpose:
prove live SSE output cannot leak non-Latin foreign-script tokens even when the model
emits them before final state sanitization.

Best seam:
unit/contract test, not a model replay.

Status:
patched in this pass.

### Candidate B - Goals strictness under concrete founder plan

Source window:
turns 24-36.

Behavior to lock:
the student gives a concrete income benchmark, ownership preference, AI-agent skill
stack, first-client target, and contract/payment proof. The extractor should stay
strict on confidence, but the analyst should avoid an endless deeper-proof loop.

Expected replay assertion:

- `income_target`, `autonomy_level`, `ownership_model`, `skill_targets`, and
  `portfolio_goal` should extract.
- Confidence can remain below done threshold if the production policy is still strict.
- The visible reply should ask one remaining proof question, not reopen already settled
  long-term fields.

### Candidate C - Goals pricing proxy loop

Source window:
turns 37-51.

Behavior to lock:
the student defines customer filters, repeat-work criteria, time-saved pricing,
pre-meeting qualification questions, and then retreats from "audit is enough" to
"must clarify scope more."

Expected replay assertion:

- `portfolio_goal` should incorporate the first-dive audit plus contract-backed paid
  delivery.
- The analyst should recognize the last turn as scope-clarification safety, not as a
  brand-new missing field.
- The final question should force the next verifiable artifact or meeting gate.

### Candidate D - Full orchestrator long-session cost

Source window:
full 51 turns.

Behavior to lock:
stage transitions work, but token fanout must stay bounded during long full-product
sessions.

Expected replay assertion:

- Thinking transitions before Purpose.
- Purpose transitions before Goals.
- No foreign-script leakage reaches streamed text.
- Tagger/context input size remains below a budget chosen before the replay.

## Current Recommendation

Do not call this trace a full-system pass. It is a successful capture through Goals with
two hard findings:

1. The live stream sanitizer gap was a confirmed bug and is patched.
2. Goals completion policy needs a product decision before code changes: strict proof
   gate versus planning-ready progression.

Next eval move: create a small Goals replay row from Candidate C, then decide whether
to change Goals completion behavior or keep it strict and only optimize wording/cost.
