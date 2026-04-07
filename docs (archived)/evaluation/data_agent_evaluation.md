# Data Agent Evaluation Guide

## Purpose
This document defines how to evaluate PathFinder's web-enabled data agents:

- `job`
- `major`
- `uni`

These stages are not pure reasoning agents. They are **retrieval-plus-reasoning** agents:

`confident_node -> analyst/tool loop -> output compiler`

The extractor still owns profile-field confidence. The analyst now also owns:

- deciding whether search is required
- forming the right query for the Vietnamese reality
- converting returned evidence into a real contradiction, validation, or Dreamer-path squeeze

This changes the evaluation seam. A data agent can fail even if its prose sounds good:

- it may skip a required search
- search with a weak or off-target query
- ignore the returned evidence
- over-trust noisy evidence
- keep confidence too high before the student survives the market-data squeeze

## Source Contracts
- Official evaluation pipeline and runner: `eval/HOW_TO_USE.md`
- Stage prompt audit rules: `docs/prompt/docs/stage_prompt.md`
- Existing stage audit log style: `docs/evaluation/stage_evaluation.md`
- Retrieval source seeds and Reddit notes: `docs/evaluation/research_sources.md`

Prompt-level contracts already in force:

- `job` must search on new `role_category` or `company_stage`
- `major` must search on new `field`
- `uni` must search on new `target_school`
- `> 0.7` confidence requires surviving a brutal data-based squeeze, not just self-report

## Evaluation Model

### 1. Retrieval Decision
Did the analyst search when the prompt contract required it?

Pass:
- searches on a new role, major field, or school claim
- skips search when nothing new was revealed and says so explicitly

Fail:
- no tool call when search was required
- redundant search spam when no new claim appeared

### 2. Query Quality
Was the query aimed at the right reality test?

Pass:
- query is Vietnam-specific when the claim is domestic
- query targets the actual squeeze: salary, curriculum, ROI, admissions, prestige, necessity, hiring
- query includes the concrete role/field/school under debate

Fail:
- generic English query with no VN constraint
- searches a side fact instead of the central contradiction
- asks for inspirational content instead of market data

### 3. Evidence Grounding
Did the analyst actually use the tool output?

Pass:
- final reasoning clearly depends on returned evidence
- identifies whether the evidence aligned, crashed, or only partially supported the student's claim

Fail:
- final reasoning could have been written before the search
- tool output is ignored or only name-dropped

### 4. Consensus Crash Quality
Did the agent convert evidence into the right squeeze?

Pass:
- evidence is cross-checked against locked priors from earlier stages
- contradiction is explicit, not vague
- `PROBE:` forces a sacrifice or zero-sum trade-off

Fail:
- analyst summarizes facts without applying them
- contradiction exists but is not embedded into the probe
- probe is generic "why?" instead of a structural squeeze

### 5. Confidence Calibration
Did the extractor respect the verification cap after the search loop?

Pass:
- extractor keeps fields at `<= 0.6` when the student has only stated a preference
- extractor only crosses `0.7` after the student survives the crash or accepts the trade-off

Fail:
- extractor upgrades confidence because the student named a title, major, or school
- extractor upgrades confidence from search evidence alone without the student's defense

### 6. Tool Discipline
Did the agent use retrieval efficiently and safely?

Pass:
- minimal searches
- no repeated search for the same unchanged claim unless the first result was clearly insufficient
- no false certainty on weak, conflicting, or snippet-level evidence

Fail:
- query loops
- shallow evidence treated as hard fact
- noisy snippets converted into overconfident conclusions

## Evaluation Layers

### Layer A. Replay Suite
This should be the primary regression suite.

Goal:
- deterministic pass/fail
- stable across time
- suitable for prompt hardening

Method:
- freeze tool outputs for a scenario
- run the graph against those frozen outputs
- assert search behavior, extractor ceilings, and analyst reasoning

Why:
- live search changes over time
- snippets drift
- pages disappear
- tuition, salary, admissions, and visa facts are time-sensitive

Status in the current repo:
- `eval/run_eval.py` already runs datasets and writes trace files
- it does **not** yet inject mocked tool results
- so replay mode is the recommended target architecture, not the current built-in capability

### Layer B. Adversarial Retrieval Suite
This is still deterministic, but the frozen search output is intentionally bad or messy.

Use it to test:
- stale snippets
- conflicting numbers
- off-country results
- SEO junk
- ambiguous school or role names

Goal:
- verify the analyst does not over-trust bad evidence
- verify follow-up search behavior or uncertainty handling

### Layer C. Live Smoke Suite
Small and occasional only.

Goal:
- detect search-tool drift
- detect query formulation regressions in the real environment

Do not use live smoke as the main regression gate because it is unstable by design.

## Short-Term Workflow vs Target Workflow

### Short-Term: What the Repo Supports Today
1. Write attack cases in `eval/*.jsonl`.
2. Run the target graph with `eval/run_eval.py`.
3. Audit traces manually in `eval/threads/.../traces/*.json`.
4. Record pass/fail and prompt patches in `docs/evaluation/*.md`.

This is enough to harden search-trigger logic and confidence ceilings, but it is weak for stable retrieval evaluation because the tool is live.

### Target Workflow: Recommended Next Step
Add a mockable search seam so the eval runner can replay fixed tool outputs.

Minimal design target:
- dataset row carries a frozen search response or fixture id
- the graph uses a test-mode search provider during eval
- traces record the exact query and the exact frozen tool payload used

Do not move the real product to mocked search. Only the evaluation path needs this seam.

## Dataset Design
Keep the dataset row shaped like normal state overlay input so it stays compatible with `eval/run_eval.py`.

Recommended row sections:

- `attack_id`: stable scenario id
- `attack_name`: short human label
- `stage.current_stage`: target data stage
- prior profiles needed for the crash
- stage queue with the student message cluster
- optional evaluator notes for manual audit

Recommended expectations to store alongside each scenario, even if checked manually at first:

- `required_search`: `true|false`
- `query_must_include`: list of required tokens or concepts
- `query_must_avoid`: optional list for bad search patterns
- `expected_crash_type`: `alignment|salary_crash|curriculum_crash|roi_crash|prestige_mismatch|necessity_crash|admissions_crash|dreamer_exception`
- `extractor_caps`: per-field max confidence before defense
- `probe_target`: field that must appear after `PROBE:`
- `probe_must_embed`: list of contradictions the probe must contain
- `done_must_be`: `true|false`

Example shape:

```json
{
  "attack_id": "job_salary_crash_01",
  "attack_name": "The Fresh-Grad Fantasy",
  "stage": { "current_stage": "job" },
  "thinking": {},
  "purpose": {},
  "goals": {
    "long": {
      "income_target": { "content": "4000 USD/thang sau khi ra truong", "confidence": 0.82 }
    }
  },
  "job_message": [
    { "type": "human", "content": "Em muon lam Data Scientist o Viet Nam, moi ra truong duoc 4k USD va remote hoan toan." }
  ],
  "_expect": {
    "required_search": true,
    "query_must_include": ["Data Scientist", "Viet Nam", "luong"],
    "expected_crash_type": "salary_crash",
    "extractor_caps": {
      "role_category": 0.6,
      "day_to_day": 0.5,
      "autonomy_level": 0.6
    },
    "probe_target": "day_to_day"
  }
}
```

## Attack Families By Stage

### Job Agent
Primary seam:
- role fantasy vs VN market structure
- salary fantasy vs goals
- day-to-day denial vs thinking/purpose priors

High-value attacks:
- **The Fresh-Grad Fantasy:** high salary claim with no market proof
- **The Glamour Title:** wants a title but cannot name the daily grind
- **The Remote Illusion:** wants fully autonomous remote work despite needing structure
- **The Niche Dreamer:** niche role with brutal market cap but strong Dreamer priors
- **The Compliance Pivot:** agrees to a safer job instantly after a crash without defending it

Expected extractor checks:
- title alone never pushes `role_category > 0.6`
- no verified grind means `day_to_day < 0.5`
- `autonomy_level` cannot lock if `day_to_day` is still weak

### Major Agent
Primary seam:
- degree necessity vs portfolio reality
- curriculum style vs learning mode
- Dreamer self-teaching vs weak local curriculum

High-value attacks:
- **The Transferability Myth:** assumes any broad major leads to the job
- **The Theory Crash:** hands-on learner picks a theory-heavy field
- **The Safe Major Drift:** picks a vague major because they are lost
- **The Dreamer Curriculum Gap:** local curriculum is weak but the student may self-teach
- **The Compliance Downgrade:** agrees to a pivot after pressure without owning the trade-off

Expected extractor checks:
- vague major claim stays `<= 0.6`
- `required_skills_coverage` stays low if the student cannot defend the bridge to the job
- do not treat search evidence alone as student verification

### University Agent
Primary seam:
- prestige requirement vs job reality
- tuition/ROI vs goals
- admissions brutality vs the student's actual runway

High-value attacks:
- **The Prestige Reflex:** picks elite school when the job does not require prestige
- **The ROI Crash:** expensive school vs modest income target
- **The Admissions Fantasy:** target school is structurally out of reach
- **The Domestic/International Blur:** vague foreign-school desire without cost or visa math
- **The Status Child:** school chosen for parental or social status, not fit

Expected extractor checks:
- naming a school does not push `target_school > 0.6`
- `prestige_requirement` stays low when market gatekeeping is unproven
- `campus_format` can be categorical, but the path is not `done` until the ROI/admissions squeeze is survived

## Trace Audit Checklist
For each trace, inspect both the tool behavior and the resulting state.

### Retrieval
- Was there a tool call when required?
- Was the query sharply targeted?
- Did the tool loop stop after enough evidence was gathered?

### Analyst Reasoning
- Did the final reasoning explicitly cite the contradiction created by the evidence?
- Did it distinguish alignment vs crash vs Dreamer exception?
- Did the `PROBE:` field match the highest-priority unresolved field?
- Did the probe force a sacrifice rather than ask for more vague detail?

### Extractor State
- Were unverified claims held under the verification cap?
- Did `done` stay `False` when the student had not yet defended the path?
- Did any field jump too high based on title-name or school-name alone?

### Output Compiler Handoff
- Was the resulting `PROBE:` clean enough for the output compiler to turn into one student-facing move?

## Failure Taxonomy
When a run fails, classify it precisely before patching prompts.

- `trigger_fail`: search should have happened but did not
- `query_fail`: search happened but targeted the wrong fact
- `grounding_fail`: evidence returned but reasoning ignored it
- `crash_fail`: evidence noted but contradiction not weaponized
- `calibration_fail`: extractor confidence rose too early
- `discipline_fail`: too many or too few searches, or weak evidence treated as hard fact
- `probe_fail`: final `PROBE:` does not carry the core contradiction

Patch the narrowest layer that caused the failure:

- trigger/query/grounding/crash/probe failures usually belong in the analyst prompt
- confidence failures belong in the extractor prompt
- repeated loop behavior may require graph-level controls later

## Recommended Documentation Pattern
Use the same audit rhythm already established in `docs/evaluation/goals_evaluation.md`:

1. Architecture and understanding
2. Vulnerabilities identified
3. Attack plan
4. Expectation map
5. Execution results
6. Attack-point checklist

For data agents, add three extra headings when useful:

7. Search trigger contract
8. Query contract
9. Evidence-to-probe contract

## Minimum Definition Of "Pass"
A data-agent attack only passes if all of the following are true:

- search behavior matched the prompt contract
- the query targeted the right VN reality test
- final reasoning used the retrieved evidence
- the contradiction was embedded into the `PROBE:`
- extractor confidence stayed under the cap until the student defended the path

If any one of those fails, the agent is not hardened yet.
