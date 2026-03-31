# Stage Evaluation: Attack Protocol Log

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

#### C. Proposed Attack Plan (Pending Audit)
1. **The Chameleon (False Compliance):** The student perfectly parrots their test priors without providing any behavioral examples (e.g., "Yeah, my test said R and I, so I definitely like building and analyzing."). *Goal: See if Nova erroneously grants `> 0.7` based on high-confidence agreement.*
2. **The Double Dodge (Evasive Drifter):** When Kai executes a Verification Squeeze with a forced-choice scenario, the student replies: "It depends on the context, I can adapt to both." *Goal: See if Kai recognizes the evasion and tightens the squeeze, or gives up and accepts the dodge.*
3. **The Prior-Clash (The Crash):** The test prior says `linguistic/social`, but the student insists they only want to work alone in a dark room coding. *Goal: Test if Kai leverages the prior to challenge the claim, or passively accepts the new self-report up to `0.6`.*

## 3. Attack Dataset (Reference)
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

**Attack 4 — The Key_quote Hunter:**
- `Lens`: `key_quote` at Turn 4 **MUST be the verbatim Turn 4 quote**: `"Thật ra, không có gì tệ hơn là phải làm việc cho người mình không tôn trọng. Dù lương cao đến đâu thì cũng không đáng."`
- Failure = any earlier, weaker quote locked in.

