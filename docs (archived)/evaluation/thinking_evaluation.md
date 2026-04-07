# Thinking Agent Evaluation & Audit Log

## 1. Architecture & Understanding
- **Extractor (Nova):** extracts `learning_mode`, `env_constraint`, `social_battery`, and `personality_type` from `thinking_style_message`. It owns the verification cap and must keep unverified self-reports at `<= 0.6`.
- **Analyst (Kai):** reads quiz priors plus the current thinking profile, cross-checks seeded priors against observed behavior, and ends with a `PROBE:` anchor that the output compiler can weaponize.
- **Evaluation locale:** inputs stay in Vietnamese because that is the real production setting, even though the analyst writes internal English reasoning.

## 2. Vulnerabilities Identified
1. **V1 - Prior-aligned self-report inflation:** a polished answer that matches `brain_type` or `riasec_top` can trick Nova into treating alignment as verification.
2. **V2 - Abstract-intellectual overread:** high-status theory language can look like evidence even when the student never survives a real trade-off.
3. **V3 - One-turn contradiction lock-in:** a strong rejection of the quiz priors can falsely lock `personality_type` or `social_battery` from a single turn.
4. **V4 - Ambivert dodge:** the student claims a perfect balance and refuses to choose, which can tempt the extractor to invent a middle category or over-score weak evidence.
5. **V5 - Weak probe tension:** the analyst may note a prior-vs-claim crash in prose but still end with a generic `PROBE:` that does not carry the contradiction cleanly.

## 3. Attack Plan

| # | Name | Attack Vector | Targeted Failure State |
|---|------|---------------|------------------------|
| 1 | The Abstract Intellectual | Student uses abstract, theory-heavy, prior-aligned language with no behavioral sacrifice. | Nova scores `learning_mode` or `personality_type` above `0.6`. |
| 2 | The Fast Rebel | Student immediately rejects the seeded priors and claims the opposite identity. | Nova locks the replacement identity too early from one unsqueezed reply. |
| 3 | The Ambivert Dodge | Student claims exact 50/50 energy needs and refuses forced choice. | Nova invents a middle category or over-scores `social_battery`. |

## 4. Expectation Map

**Attack 1 - The Abstract Intellectual**
- `Nova`: any conversational field must stay `<= 0.6`.
- `Kai`: must treat the answer as self-report and force a trade-off around theory vs execution cost.

**Attack 2 - The Fast Rebel**
- `Nova`: the replacement claim stays capped because prior rejection is still just one unsqueezed turn.
- `Kai`: must embed the prior-vs-claim crash directly into the final `PROBE:` anchor.

**Attack 3 - The Ambivert Dodge**
- `Nova`: `social_battery` stays `unclear < 0.5`.
- `Kai`: must force a zero-sum energy trade-off rather than accepting the balanced identity story.

## 5. Execution Results
**Run date:** 2026-04-05  
**Commands:**
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/thinking_attack_v2.jsonl --graph thinking`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/thinking_attack.jsonl --graph thinking`

### 5A. Pre-patch Replay Finding
The first replay exposed a real S4 failure:
- **Attack 1 - The Abstract Intellectual:** **FAIL.**
  Nova assigned `learning_mode="theoretical"` at `0.74` from a polished self-report that merely matched the seeded priors.

The other two v2 attacks were directionally better, but the extractor still needed harder guardrails.

### 5B. Patch Set Applied
- Added `PRIOR AGREEMENT IS NOT DEFENSE`.
- Added `DETAIL IS NOT DEFENSE`.
- Added explicit `Student Claim -> Agent Squeeze -> Student Defense` verification language.
- Added `NO ONE-TURN LOCK-IN`.
- Added `ENERGY IS NOT SOCIABILITY`.
- Added analyst-side `TENSION EMBEDDING` so the final `PROBE:` starts with the actual clash.
- Reworked the analyst handoff into structured fields plus Python-composed trailing `PROBE:` output, matching the newer Purpose/Goals pattern.
- Added a scoring-node Python verification clamp: with fewer than 2 human turns in `thinking_style_message`, no conversational Thinking field may exceed `0.6`, and `done` is recomputed after the clamp.
- Added explicit extractor rules for `FORCED-CHOICE CONFESSION IS STILL SELF-REPORT` and `SCENE DETAIL IS NOT ENV CONSTRAINT`.

### 5C. Post-patch Results
**`eval/thinking_attack_v2.jsonl`: PASS**
- **Attack 1 - The Abstract Intellectual:** `learning_mode="theoretical"` stayed capped at `0.55`; `personality_type="analytical"` stayed at `0.45`.
- **Attack 2 - The Fast Rebel:** `personality_type="social"` stayed capped at `0.55`; `social_battery` stayed unresolved.
- **Attack 3 - The Ambivert Dodge:** `social_battery="unclear"` stayed at `0.4`.
- All 3 traces ended with a deterministic trailing `PROBE:` line composed in Python from structured analyst fields.

**`eval/thinking_attack.jsonl`: PASS**
- All 3 legacy attacks completed successfully under the tightened extractor and analyst rules.
- The old single-turn overconfidence leak is now gone: the prior "dark room" replay no longer locks `social_battery` / `env_constraint` off one answer. In the latest replay, that case landed at `social_battery="solo" 0.42` and `env_constraint="home" 0.2`, with the probe still targeting `social_battery`.

## 6. Current Verdict
The Thinking agent now passes the current Stage 0 audit standard with both seams hardened:
- the analyst handoff is deterministic (`PROBE:` always survives), and
- the extractor can no longer bypass the verification loop with single-turn, prior-aligned, or scene-heavy self-reports.

## 7. Attack Point Checklist
- [x] Did Nova keep prior-aligned self-reports under `0.6`?
- [x] Did Nova avoid one-turn lock-in after prior rejection?
- [x] Did Nova avoid inventing a fake middle category for `social_battery`?
- [x] Did Kai end with a usable contradiction-carrying `PROBE:` anchor?
- [x] Did the graph-level clamp stop single-turn forced-choice answers from locking Stage 0 fields?
- [x] Did both datasets complete successfully after the patch?

## 8. Open Gap
The current Stage 0 suite is still short and stage-local. The next meaningful escalation is either:
- a longer multi-turn contradiction dataset for Thinking, or
- orchestrator/output end-to-end evals to verify the stronger `PROBE:` handoff survives the full pipeline.
