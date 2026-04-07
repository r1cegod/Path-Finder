# Job Agent Evaluation & Audit Log

## 1. Architecture & Understanding
- **Extractor (Nova):** Extracts `role_category`, `company_stage`, `day_to_day`, and `autonomy_level` from the `job_message` queue. It must enforce the verification cap so a named job title or company type stays `<= 0.6` until the student survives a market-data squeeze.
- **Analyst (Tess):** Reads `thinking`, `purpose`, `goals`, `message_tag`, current `job` state, and `stage_reasoning.job`. It owns search-trigger decisions, Vietnam-specific query formulation, evidence grounding, and the final `PROBE:` anchor for the output compiler.
- **Evaluation seam:** This is a retrieval-plus-reasoning stage. A pass requires more than good prose. The run must search when required, form a sharp VN-market query, use the evidence in the reasoning, embed the contradiction into `PROBE:`, and keep extractor confidence under the verification cap until the student defends the path.
- **Evaluation locale:** Student-facing inputs remain Vietnamese because the real product serves Vietnamese students, even though the analyst writes internal English reasoning.

## 2. Vulnerabilities Identified
1. **V1 - Prompt/state drift in the extractor:** `JOB_CONFIDENT_PROMPT` asks for `key_quote`, but `JobProfile` in state does not contain `key_quote`. This is a contract mismatch and raises the risk of confused extraction behavior.
2. **V2 - Title-first overconfidence:** The extractor currently has the right verification-cap language, but it does not explicitly punish glamour-title claims that name a role without naming the grind.
3. **V3 - Weak dependency enforcement:** The analyst says `day_to_day` must be verified before `autonomy_level` or `role_category` can lock, but the extractor prompt does not mirror that dependency explicitly.
4. **V4 - Missing explicit tension-embedding rule:** The analyst prompt asks for a Socratic trade-off, but it does not yet explicitly force the final `PROBE:` to carry the exact prior-vs-market contradiction.
5. **V5 - Dreamer-exception ambiguity:** The analyst has a Dreamer rule, but the threshold for when to validate ambition vs when to crush fantasy is still underspecified and needs trace verification.

## 3. Attack Plan

| # | Name | Attack Vector | Targeted Failure State |
|---|------|--------------|------------------------|
| 1 | The Fresh-Grad Fantasy | Student wants `Data Scientist` in Vietnam, fully remote, with very high fresh-grad pay. | No search, weak salary query, or extractor locks the title/autonomy too early. |
| 2 | The Glamour PM | Student picks `Product Manager` but wants solo deep work and hates meetings/conflict. | Analyst fails to use market reality against `thinking.social_battery`; probe stays generic. |
| 3 | The Remote Freelancer Illusion | Student wants freelance UI/UX with total schedule freedom despite strong structure/collaboration priors. | Analyst skips or weakens the autonomy crash; extractor locks autonomy from self-report. |
| 4 | The Niche Dreamer | Student wants a niche creative role in Vietnam with strong Dreamer priors already established. | Analyst crushes the ambition instead of validating the Dreamer path and probing the concrete barrier. |

## 4. Expectation Map

**Attack 1 - The Fresh-Grad Fantasy**
- `Nova`: `role_category`, `company_stage`, and `autonomy_level` must stay `<= 0.6`; `day_to_day` must stay weak if the student cannot name the grind.
- `Tess`: must search with a Vietnam-specific salary or market-reality query, then embed the pay/remote reality crash into `PROBE:`.

**Attack 2 - The Glamour PM**
- `Nova`: `role_category` may reach the self-report cap, but `day_to_day` must stay `< 0.5` and `autonomy_level` must not lock.
- `Tess`: must use PM market/day-to-day evidence and embed the contradiction between meetings/stakeholder work vs the student's solo-deep-work prior directly into `PROBE:`.

**Attack 3 - The Remote Freelancer Illusion**
- `Nova`: total-autonomy claims must remain capped until the student survives the grind test.
- `Tess`: must search against the actual freelance/UI-UX execution reality in Vietnam and force a structure-vs-freedom sacrifice in `PROBE:`.

**Attack 4 - The Niche Dreamer**
- `Nova`: niche-role desire alone must stay capped.
- `Tess`: must search the Vietnam market constraint, but if `purpose` and `goals` show a real Dreamer profile, the reasoning should validate the hard path and probe the concrete execution barrier instead of redirecting to the safe path.

## 5. Execution Results
**Run date:** 2026-04-05  
**Command:** `venv\Scripts\python eval/run_eval.py --mode multi --file eval/job_attack.jsonl --graph job`

### 5A. Draft Refactor Applied
The old direct tool loop was replaced with a dedicated Stage 3 research seam:
- `confident_node` keeps extractor confidence capped.
- `job_research_planner` decides whether research is needed and emits one narrow contradiction-focused search query.
- `job_researcher` calls OpenAI `responses.create(..., tools=[{"type": "web_search"}])` with a domain allowlist from `backend/data/contracts/research_sources.py`.
- `job_synthesizer` reads the structured `job_research` packet and writes the final `stage_reasoning.job`.

This also added a new state field:
- `job_research` in `PathFinderState`

Prompt changes for the draft:
- `JOB_CONFIDENT_PROMPT` keeps the self-report cap and day-to-day-first rules.
- `JOB_RESEARCH_PLAN_PROMPT` forces atomic query planning instead of giant mixed research requests.
- `JOB_SYNTHESIS_PROMPT` now consumes `job_research` rather than raw tool chatter.

### 5B. Draft Verification
**Import verification:**
- `venv\Scripts\python -c "from backend.data.state import JobResearch; print('state-ok')"`
- `venv\Scripts\python -c "from backend.job_graph import job_graph; print('job-graph-ok')"`

**Replay command:** `venv\Scripts\python eval/run_eval.py --mode multi --file eval/job_attack.jsonl --graph job`

Runtime result:
- 4 inputs
- 4 succeeded
- 0 failed

### 5C. Replay Findings
**Attack 1 - The Fresh-Grad Fantasy:** **PASS.**
- The planner narrowed the contradiction to Vietnam fresher Data Scientist salary reality.
- Research produced concrete salary bands and fresher postings.
- Final reasoning correctly crushed the `100M VND/month right after graduation` fantasy and preserved a `PROBE:` about real first-year grind.

**Attack 2 - The Glamour PM:** **PASS.**
- The planner targeted PM stakeholder load rather than title prestige.
- Research returned recurring evidence that PM work is cross-functional and meeting-heavy.
- Final reasoning preserved the contradiction between solo deep work and PM reality.

**Attack 3 - The Remote Freelancer Illusion:** **PASS.**
- The planner targeted remote/freelance UI/UX autonomy in the Vietnam market.
- Research showed that remote/freelance roles exist but usually still include meetings, reporting, and team coordination.
- Final reasoning preserved the structure-vs-freedom contradiction instead of drifting into generic encouragement.

**Attack 4 - The Niche Dreamer:** **PASS.**
- The planner treated the case as a market-availability check, not a fantasy crush by default.
- Research showed concept artist roles exist but are niche, location-clustered, and often skew mid-level.
- Final reasoning preserved the Dreamer exception while grounding it in sparse-role and long-portfolio-grind reality.

**Current verdict:**
- The draft works. All 4 attacks now produce a populated research packet and a non-empty `stage_reasoning.job` with a trailing `PROBE:`.
- The major failure mode has shifted from handoff collapse to evidence quality. OpenAI web search is materially better than the old giant-query Serper path, but cited source lists can still include noisy or weakly relevant pages.
- There are also trace-time Pydantic serializer warnings around structured outputs. They did not break the run, but they should be cleaned up before treating the architecture as fully settled.

## 6. Attack Point Checklist
- [x] Did Tess search on every new `role_category` or `company_stage` claim?
- [x] Were queries Vietnam-specific and aimed at the real contradiction?
- [x] Did the reasoning clearly depend on retrieved evidence when evidence was present?
- [x] Did `PROBE:` survive every trace after tool use?
- [x] Did `PROBE:` carry the contradiction rather than collapse into a generic follow-up?
- [x] Did Nova keep unverified job-title claims under the self-report cap?
- [x] Did `day_to_day` stay weak when the student could not name the grind?
- [x] Did the Dreamer exception validate grit without collapsing into fantasy approval?
