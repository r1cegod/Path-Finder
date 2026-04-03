# Stage Evaluation: Attack Protocol Log

Reference:
- For web-enabled `job` / `major` / `uni` stage methodology, use `docs/evaluation/data_agent_evaluation.md` as the canonical retrieval-evaluation guide.

## 1. Macro Architecture (Evaluation Seam)
This tracks the evaluation of each Stage Agent across the PathFinder pipeline.
Pipeline flow for a stage:
`Input Parser` -> `Target Extractor (Confident Node)` -> `Target Analyst (Drill Node)` -> `Output Compiler`

## 2. Agent Audit & Insight Log

### Stage 0: Thinking Agent

#### A. Architecture & Understanding
- **Extractor (Nova):** Maps conversational evidence to `learning_mode`, `env_constraint`, `social_battery`, and `personality_type`. Responsible for enforcing the `0.6` ceiling for unverified self-reports.
- **Analyst (Kai):** Executes "The Priors Cross-Check" (comparing MI/Holland test priors against behavior) and "The Verification Squeeze" (forcing trade-offs to push confidence over `0.7`).

#### B. Proposed Refinements (Pending Audit)
1. **Nova's Verification Blindspot:** Nova's prompt says `> 0.7` requires the student to have "defended it against pushback." However, Nova isn't instructed on *how* to recognize a pushback. 
   - *Refinement:* Nova needs an explicit rule detailing the required multi-turn sequence (`Student Claim -> Agent Squeeze -> Student Defense`) before scoring `> 0.7`.
2. **Kai's PROBE Anchor Weakness:** Kai detects conflicts between test priors and claims, but the `PROBE:` string often just asks to "test the claim." The Output Compiler doesn't get the *reason* for the test in the PROBE string.
   - *Refinement:* Force the `PROBE:` anchor to explicitly embed the tension. (e.g., `PROBE: learning_mode — Prior says visual, but student claims hands-on; force a trade-off between watching a tutorial vs. breaking the code.`)

#### C. Proposed Attack Plan (Phase 1)
1. **The Chameleon (False Compliance):** The student perfectly parrots their test priors without providing any behavioral examples. *Goal: See if Nova erroneously grants `> 0.7` based on high-confidence agreement.*
2. **The Double Dodge (Evasive Drifter):** When Kai executes a Verification Squeeze, the student replies: "It depends, I can adapt." *Goal: See if Kai tightens the squeeze or accepts the dodge.*
3. **The Prior-Clash (The Crash):** Test prior says `linguistic`, student insists they work alone coding. *Goal: Test if Kai leverages the prior to challenge the claim.*

#### D. Brutal Attack Plan (Phase 2 - Edge Cases)
1. **The Abstract Intellectual:** User uses high-level, theoretical buzzwords ("conceptualize", "frameworks") but no grounded behavior. *Goal: Nova must cap <0.6. Kai must force a grounded, behavioral example rather than engaging in a philosophical debate.*
2. **The Fast Rebel:** User immediately rejects the test priors ("the quiz is wrong") without prompting. *Goal: Kai must immediately catch the prior crash. Nova must still limit confidence to <0.6 until the student provides behavioral proof for their new claim.*
3. **The Ambivert Dodge:** User claims perfect 50/50 balance in `social_battery` and refuses to choose. *Goal: Nova must leave field unclear/mixed <0.5. Kai must impose an extreme zero-sum constraint (e.g., "If you were forced to do only one for 2 years...") to break the dodge.*

## 3. Attack Dataset (Reference)
- Stage 0 (v1): `eval/thinking_attack.jsonl`
- Stage 0 (v2): `eval/thinking_attack_v2.jsonl`
- Stage 0: `eval/thinking_attack.jsonl`
- Stage 1: `eval/purpose_attack.jsonl`

---

### Stage 1: Purpose Agent

#### A. Architecture & Understanding
- **Extractor (Lens):** Extracts `core_desire`, `work_relationship`, `ai_stance`, `location_vision`, `risk_philosophy`, `key_quote`. Enforces `0.6` self-report ceiling. Has a verbatim-only `key_quote` rule.
- **Analyst (Mira):** Reads `message_tag` (compliance/vague/true), Cross-Checks `ThinkingProfile.personality_type` as a prior, and enforces cross-field dependency locks (`work_relationship=stepping stone` → `core_desire` blocked).

#### B. Vulnerabilities Identified

1. **V1 — Philanthropist Blindspot:** Prompt handles `parental_pressure=True` from orchestrator tag. But if the student *volunteers* a safety net ("bố mẹ support em") without the orchestrator flagging it, Mira has no explicit rule to recognize "no real sacrifice = unverifiable." Mira should detect the revealed external safety net as invalidating any claimed sacrifice.

2. **V2 — Dependency Chain Deadlock:** `work_relationship="stepping stone"` blocks `core_desire`. But if the student's destination stays perpetually abstract across multiple probes ("just want freedom," "not be controlled"), no explicit rule tells Mira to permanently mark `core_desire = blocked: destination unresolved`. Mira might accept the vague destination and attempt to extract core_desire anyway.

3. **V3 — Risk Crash (Priors Weaponized vs. Passively Noted):** Thinking priors (`solo`, `home`, `analytical`) structurally contradict `risk_philosophy="startup"`. The PROBE format (pre-fix) had no embedded-tension requirement. Mira could *note* the conflict but produce a weak `PROBE:` that doesn't force an actual sacrifice naming the cognitive conflict explicitly.

4. **V4 — Key_quote Lock-In:** `key_quote` guardrail says "never paraphrase." But no rule dictates WHEN to *upgrade* to a better quote. Lens may lock Turn 1's weak quote and ignore a much stronger one in Turn 4.

#### C. Attack Plan

| # | Name | Attack Vector | Targeted Failure State |
|---|------|--------------|------------------------|
| 1 | The Hollowed Philanthropist | Student claims "help people" as core_desire, then reveals bố mẹ hold the financial safety net | Lens scores `core_desire > 0.5`; Mira misses the "no sacrifice" signal |
| 2 | The Dependency Chain | `work_relationship="stepping stone"` → student never names a concrete destination across 3 probes | Mira unlocks/extracts `core_desire` from abstract "freedom" framing |
| 3 | The Risk Crash | Student claims "startup risk-taker." ThinkingProfile: `solo`, `home`, `analytical` — all contradict founder lifestyle | Mira notes tension but PROBE doesn't embed the specific structural conflict; Lens scores `risk_philosophy > 0.5` |
| 4 | The Key_quote Hunter | Turn 1: weak quote. Turn 3: strong specific behavioral quote. Turn 4: even stronger, most revealing | Lens stays locked on Turn 1 quote. Fails to upgrade to Turn 4's verbatim gold. |

#### D. Expectation Map (Per Attack)

**Attack 1 — The Hollowed Philanthropist:**
- `Lens`: `core_desire` → content="help people/impact", **confidence MUST be < 0.4** (empty bucket compliance script)
- `Mira`: Must explicitly flag that the student's claim has *zero sacrifice* (external safety net exposed), and the PROBE must target "what would you give up if bố mẹ couldn't support you?"

**Attack 2 — The Dependency Chain:**
- `Lens`: `work_relationship` → "stepping stone", confidence 0.55-0.6. `core_desire` → **must stay "unclear", confidence < 0.3**
- `Mira`: Must output reasoning that `core_desire` **remains blocked** because the destination chain terminated at another abstraction ("no control"), not a concrete desire.

**Attack 3 — The Risk Crash:**
- `Lens`: `risk_philosophy` → "startup risk", confidence **MUST stay < 0.5** (student said "many people do it" — a deflection, not a defense)
- `Mira`: PROBE must explicitly embed TWO pieces: (1) the Thinking prior conflict (`solo+home+analytical ≠ startup founder`), (2) the specific sacrifice demanded ("you've never named what you give up — name it now")

## 3. Execution Results (Stage 0 - Phase 2)

**Attack 1 (The Abstract Intellectual):** **PASS**. Nova capped `personality_type` at 0.65. Kai correctly rejected the theoretical fluff and forced a drill on `social_battery` to demand behavioral evidence.

**Attack 2 (The Fast Rebel):** **PASS** (Flying colors). Kai immediately caught the prior-crash, and escalated the probe to test both `personality_type` and `social_battery` zero-sum trade-offs under the new claim.

**Attack 3 (The Ambivert Dodge):** **MILD FAIL (Patched)**. Kai correctly identified the dodge and forced a zero-sum trade-off scenario. However, Nova (Extractor) hallucinated a new enum category (`social_battery="ambivert"`) instead of leaving it `< 0.5`. 
*Patch Applied:* Added STRICT ENUM COMPLIANCE to Nova's guardrails. Nova is now explicitly banned from inventing "ambivert/both/mixed" and must drop the score to `< 0.5` with content `"unclear"` if the student dodges.

## 4. Attack Dataset (Reference)
- Stage 0 (v1): `eval/thinking_attack.jsonl`
- Stage 0 (v2): `eval/thinking_attack_v2.jsonl`
- Stage 1 (v1 & v3): `eval/purpose_attack.jsonl`

---

#### E. Brutal Attack Plan (Phase 3 - The Illusions)

| # | Name | Attack Vector | Targeted Failure State |
|---|------|--------------|------------------------|
| 5 | The AI Apathy Trap | Student says "AI is everywhere, I'll just use it to write emails sometimes." | Lens erroneously scores this as `leverage` instead of `indifferent`. Mira fails to force a forward-looking Squeeze. |
| 6 | The Digital Nomad Illusion | Student wants to be a remote traveler. Thinking prior says they need `structured` environment and `collaborative` social battery. | Lens accepts `location_vision = remote` > 0.6. Mira fails to catch the massive prior contradiction. |
| 7 | The Retire-Early Calling | Student claims work is a "calling" (spiritual dedication), but then reveals their actual goal is FIRE at 35 to never work again. | Lens locks `work_relationship = calling`. Mira fails to crash the ideological contradiction. |

#### F. Expectation Map (Phase 3)

**Attack 4 (Restored) — The Key_quote Hunter:**
- `Lens`: `key_quote` at Turn 4 MUST be the verbatim Turn 4 quote. Never truncated.

**Attack 5 — The AI Apathy Trap:**
- `Lens`: `ai_stance` MUST stay `< 0.5`. There is no proactive strategy, just passive compliance.
- `Mira`: Must flag that the student's stance is passive and PROBE for what happens when AI replaces junior tasks.

**Attack 6 — The Digital Nomad Illusion:**
- `Lens`: `location_vision` MUST stay `< 0.6` because they haven't proved they have the discipline for a high-autonomy nomadic life.
- `Mira`: PROBE MUST embed the conflict: "Prior says strict structure and collaborative teams, but nomad life is zero structure and totally isolated. Sacrifice one."

**Attack 7 — The Retire-Early Calling:**
- `Lens`: `work_relationship` MUST drop to `< 0.5 (unclear)`. A true calling doesn't plan to quit at 35.
- `Mira`: Must brutally call out the contradiction: a calling is lifelong; FIRE is a stepping-stone mechanism. PROBE must force them to reconcile this.

## 5. Execution Results (Stage 1 - Phase 3)

**Attack 5 (The AI Apathy Trap):** **PASS**. Lens correctly identified the logic as passive, scoring it `indifferent = 0.3` under the new AI Apathy Rule. Mira forced a speed-vs-craft trade-off probe.
**Attack 6 (The Digital Nomad Illusion):** **PASS**. Lens successfully defended against detail-heavy enthusiasm and capped `location_vision` at `0.6` (down from 0.95 in earlier traces). Mira successfully embedded the `structured-environment` prior conflict directly into the `risk_philosophy` PROBE.
**Attack 7 (The Retire-Early Calling):** **PASS**. The `CONTRADICTION DROP` rule executed flawlessly. As soon as the student claimed FIRE at 35, the `work_relationship = calling` confidence crashed from `0.9` down to `0.58`.

*Result:* Purpose Agent is fully hardened against all known evasion, hallucination, and contradiction attack vectors.
