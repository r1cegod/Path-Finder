# Purpose Agent Evaluation & Audit Log

## 1. Architecture & Understanding
- **Extractor (Lens):** Extracts `core_desire`, `work_relationship`, `ai_stance`, `location_vision`, `risk_philosophy`, and `key_quote`. Enforces the verification cap, contradiction drops, and purpose-stage-specific hard bans such as safety-net support and travel-fantasy overconfidence.
- **Analyst (Mira):** Reads `thinking`, `message_tag`, `user_tag`, current `purpose` state, and prior `stage_reasoning.purpose`. It owns cross-field blocking, prior-vs-claim tension detection, and the final `PROBE:` handoff to the output compiler.
- **Evaluation locale:** Stage 1 is evaluated with Vietnamese student turns from `eval/purpose_attack.jsonl`, while the agent itself still writes internal English reasoning.

## 2. Vulnerabilities Identified
1. **V1 - Safety-Net False Sacrifice:** Students can sound mission-driven while hiding behind parental funding, which should block verification rather than count as sacrifice.
2. **V2 - Dependency Chain Drift:** `work_relationship="stepping stone"` can tempt the extractor to invent a concrete `core_desire` even when the destination is still only abstract avoidance.
3. **V3 - Prior Crash Dilution:** The analyst may note a Thinking-prior clash in prose, then soften the final `PROBE:` instead of carrying the actual contradiction into the handoff.
4. **V4 - AI Convenience Inflation:** Passive AI convenience can be mistaken for a real `leverage` stance.
5. **V5 - Lifestyle Fantasy Inflation:** Digital-nomad detail can sound concrete enough to over-lock `location_vision`.
6. **V6 - Calling vs Escape Deadlock:** Passion language can stay artificially high even after the student explicitly reframes work as a temporary vehicle toward FIRE and total retirement.

## 3. Attack Plan

| # | Name | Attack Vector | Targeted Failure State |
|---|------|---------------|------------------------|
| 1 | The Hollowed Philanthropist | Student claims social impact, then reveals the family covers the downside. | Lens treats support-backed sacrifice as verified purpose. |
| 2 | The Dependency Chain | Work is only a means, but the destination never becomes concrete. | Lens extracts a fake `core_desire` from abstract escape language. |
| 3 | The Risk Crash | Student claims startup-risk identity but only offers motivational fluff after a squeeze. | Lens leaves `risk_philosophy` too high; Mira drops the structural crash from the handoff. |
| 4 | The Key_quote Hunter / Control Aversion | Student reveals a much stronger anti-control line later in the exchange. | Lens stays on weak early wording or overstates calling. |
| 5 | The AI Apathy Trap | Student treats AI as incidental convenience. | Lens inflates `ai_stance`; Mira fails to push the real work-ownership question. |
| 6 | The Digital Nomad Illusion | Student paints a vivid remote-travel lifestyle that clashes with thinking-stage priors. | Lens mistakes vivid detail for proof and over-locks `location_vision`. |
| 7 | The Retire-Early Calling | Student says work is a calling, then says the real goal is FIRE and full retirement by 35. | Lens preserves `calling`; Mira drifts to softer probing instead of forcing the contradiction. |

## 4. Patch Set Applied
- Reworked `backend/purpose_graph.py` so Mira now returns structured fields (`purpose_summary`, `probe_field`, `probe_tension`, `probe_instruction`) and Python always composes the final trailing `PROBE:` line.
- Injected `user_tag` into the analyst prompt so Stage 1 can read persistent tags like `parental_pressure` and `reality_gap` instead of referencing data it never received.
- Hardened the analyst prompt in `backend/data/prompts/purpose.py` with:
  - Safety-net invalidation
  - explicit blocked-destination handling for stepping-stone logic
  - explicit calling-vs-FIRE contradiction handling
  - explicit tension embedding in `probe_tension`
- Hardened the extractor prompt with:
  - hard `<= 0.6` self-report cap language
  - `STEPPING-STONE DESTINATION RULE`
  - `CALLING VS ESCAPE RULE`
  - `CONTRADICTION PRIORITY RULE`
  - `LOCATION FANTASY CAP`

## 5. Execution Results
**Run date:** 2026-04-05  
**Command:** `venv\Scripts\python eval/run_eval.py --mode multi --file eval/purpose_attack.jsonl --graph purpose`

**Attack 1 - The Hollowed Philanthropist:** **PASS.**
- `Lens` kept `core_desire = environment and social inequality` at `0.35`, preserving the social-impact signal without treating it as verified sacrifice.
- `Mira` carried the safety-net contradiction directly into the handoff:
  `PROBE: core_desire - safety-net support cancels the sacrifice ...`

**Attack 2 - The Dependency Chain:** **PASS.**
- `Lens` held `work_relationship = stepping stone` at `0.6` and kept `core_desire = unclear` at `0.2`, which preserves the blocked-destination logic.
- `Mira` kept the probe on the unresolved freedom-vs-stability trade-off instead of pretending the destination was already known.

**Attack 3 - The Risk Crash:** **PASS.**
- `Lens` kept `risk_philosophy = unclear` at `0.4`.
- `Mira` turned the startup claim into a real downside test instead of accepting the motivational dodge.

**Attack 4 - Control Aversion / Quote Upgrade:** **PASS.**
- `Lens` preserved the anti-control signal as low-confidence purpose evidence rather than turning it into a false calling lock.
- The trace retained a stronger later quote rather than staying stuck on weaker early wording.

**Attack 5 - The AI Apathy Trap:** **PASS.**
- `Lens` kept `ai_stance = indifferent` at `0.3`.
- `Mira` escalated from AI convenience into the deeper work-ownership question rather than accepting passive tooling as a worldview.

**Attack 6 - The Digital Nomad Illusion:** **PASS.**
- `Lens` capped `location_vision = remote` at `0.6`, which is the intended fantasy ceiling for vivid but unverified nomad claims.
- `Mira` embedded the actual prior clash (`social, collaborative structure` vs `extreme solo autonomy and unstructured mobility`) in the final `PROBE:` line.

**Attack 7 - The Retire-Early Calling:** **PASS.**
- `Lens` dropped `work_relationship` to `stepping stone (0.45)` and kept `core_desire` unclear/low.
- `Mira` kept the contradiction attached to `work_relationship`:
  `PROBE: work_relationship - calling vs total retirement after FIRE ...`

## 6. Residual Risk
- Attack 6 still routes the final probe through `risk_philosophy` in some runs instead of `location_vision`, even though the contradiction text is preserved. The stage-local behavior is acceptable because the extractor cap now holds and the handoff still carries the structural clash, but it remains a stylistic instability worth watching in future end-to-end tests.
- Purpose-stage evaluation is still stage-local. The next stronger test is orchestrator/output end-to-end replay to confirm the Vietnamese student-facing response preserves Mira's new contradiction-rich `PROBE:` anchors.

## 7. Attack Point Checklist
- [x] Did Lens keep safety-net-backed sacrifice below verification?
- [x] Did Lens keep abstract stepping-stone destinations as `core_desire = unclear`?
- [x] Did Lens keep startup-risk talk below lock without a real sacrifice?
- [x] Did Lens keep passive AI use below `leverage`?
- [x] Did Lens cap digital-nomad fantasy at the location-vision ceiling?
- [x] Did Lens break the calling lock when FIRE/total retirement appeared?
- [x] Did Mira preserve a trailing `PROBE:` anchor on every trace?
- [x] Did Mira carry the actual contradiction or missing-proof text into the handoff?
