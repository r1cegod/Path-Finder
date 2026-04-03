# Goals Agent Evaluation & Audit Log

## 1. Architecture & Understanding
- **Extractor (Scale):** Extracts `long` horizon (`income_target`, `autonomy_level`, `ownership_model`, `team_size`) and `short` horizon (`skill_targets`, `portfolio_goal`, `credential_needed`). Enforces VERIFICATION CAP (<0.6 for unverified self-reports).
- **Analyst (Silo):** Executes "The Priors Cross-Check" (checking Purpose priors like `risk_philosophy` against `ownership_model`) and "The Horizon Squeeze" (validating 5-year ambition against 1-year execution plan).

## 2. Vulnerabilities Identified
1. **V1 — The Numbers Hallucination:** Student says "I want to be a millionaire" or "rich". Scale might invent an `income_target` > 0.7 without actual metrics. 
2. **V2 — The Abstract Skills evasion:** Student says "I want to learn communication and leadership". Scale extracts "communication" as `skill_targets` > 0.7. Silo accepts without forcing technical/hard skills verification.
3. **V3 — The Credentialed Founder (Horizon Gap):** Student wants to be a `founder` (Long) but their short-term plan is entirely soft (`credential_needed = degree`, `portfolio_goal = none`). Silo might fail to trigger the Horizon Squeeze to punish this gap.
4. **V4 — The Risk Crash (Prior evasion):** Purpose prior says `risk_philosophy = gov stability`. Student now claims `ownership_model = freelance`. Silo notes it but fails to explicitly embed the tension in the PROBE anchor.

## 3. Attack Plan (Phase 1)

| # | Name | Attack Vector | Targeted Failure State |
|---|------|--------------|------------------------|
| 1 | The Abstract Millionaire | Student uses empty bucket words ("rich", "successful") with no numbers. | Scale invents/scores `income_target` > 0.5. Silo fails to demand numbers. |
| 2 | The Credentialed Founder | `ownership_model = founder` (Long) but `portfolio_goal = none` & `credential_needed = degree` (Short). | Silo accepts the academic safety-net instead of triggering the Horizon Squeeze. |
| 3 | The Prior-Crashing Freelancer | `purpose.risk_philosophy = gov stability` but current goal is `ownership_model = freelance`. | Silo forgets to embed the clash in the PROBE anchor text. |

## 4. Expectation Map (Per Attack)

**Attack 1 — The Abstract Millionaire:**
- `Scale`: `income_target` MUST stay `< 0.5 (unclear)`. 
- `Silo`: PROBEMUST demand a concrete number and timeframe.

**Attack 2 — The Credentialed Founder:**
- `Scale`: `ownership_model = founder` capped at 0.6. `portfolio_goal = none` > 0.7.
- `Silo`: MUST flag the HORIZON GAP (Ambition vs Execution). PROBE must force them to name the 1-year verifiable artifact that justifies calling themselves a founder.

**Attack 3 — The Prior-Crashing Freelancer:**
- `Scale`: `ownership_model = freelance` capped at 0.6. 
- `Silo`: PROBE MUST directly embed the tension: "Your purpose prioritizes government stability, but freelancing is total financial instability. Sacrifice one."

---

## 5. Execution Results (Stage 2 - Phase 1)
*Pending Execution...*

---

## 6. Attack Point Checklist
- [ ] Did Scale strictly enforce the 0.6 cap on unverified self-reports?
- [ ] Did Scale block empty bucket words ("rich", "soft skills") with < 0.5?
- [ ] Did Silo successfully execute the Horizon Squeeze (Ambition vs 1-year plan)?
- [ ] Did Silo explicitly embed the Purpose Prior clash into the `PROBE:` anchor string?
- [ ] Was the output compiler handed a perfectly clean 1-sentence PROBE?
