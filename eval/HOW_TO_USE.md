# PathFinder Evaluation Pipeline

`eval/HOW_TO_USE.md` is the single official workflow for creating, running, and closing evaluation work in this repo.

Use this file for:
- the evaluation workflow
- the production-first evaluation rules
- runner commands and trace locations
- the context docs required before starting

Other docs may hold evaluation context or stage-specific findings, but they should point back here for the actual pipeline.

Sub-orchestrator-only prompt and memory-maintenance audits now use a separate focused lane:
- `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\evaluation\sub_orchestrator_focus_eval_how_to_use.md`
- `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\evaluation\sub_orchestrator_evaluation.md`

---

## Purpose

PathFinder evaluations are not just runner commands. They are a production-hardening workflow.

An evaluation cycle is only complete when it:
- starts from an explicit production behavior target
- follows a capped round plan instead of open-ended hardening
- creates or updates the right audit log
- runs replay attacks
- audits trace behavior, not just runtime success
- discusses meaningful user-facing behavior changes with the user
- records the final result in the canonical vault docs

Manual spot checks in LangGraph Studio are not enough.

---

## Available Context

Read these before non-trivial evaluation work:

- Project router: `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\README.md`
- Stable project facts: `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\context\docs\PROJECT_CONTEXT.md`
- Live work and blockers: `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\context\docs\CURRENT_CONTEXT.md`
- Architecture source of truth: `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\architecture\docs\ARCHITECTURE.md`
- State contract: `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\architecture\docs\state_architecture.md`
- Stage prompt rules: `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\prompt\docs\stage_prompt.md`
- Output prompt rules: `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\prompt\docs\output_prompt_architecture.md`
- Prompt implementation guide: `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\prompt\how to\production_system_prompts.md`
- Evaluation umbrella log: `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\evaluation\stage_evaluation.md`

Use stage-specific evaluation logs when relevant:

- `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\evaluation\thinking_evaluation.md`
- `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\evaluation\purpose_evaluation.md`
- `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\evaluation\goals_evaluation.md`
- `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\evaluation\job_evaluation.md`
- `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\evaluation\data_agent_evaluation.md`
- `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\evaluation\research_sources.md`

---

## Production-First Workflow

Follow this loop in order. Do not jump straight to JSONL authoring or runner commands.

### Round Gate: Max 3 Rounds Before Production Ready

Every production-hardening evaluation plan must be capped at **3 rounds total**.

Rules:
- a plan may contain **at most 3 rounds**
- each round may finish **exactly 1 stage** only
- after each round, stop and hand over the updated evaluation log
- after each round, start a user conversation before moving to the next round
- do not batch multiple stage signoffs into one giant evaluation pass

Minimum round shape:
- Round 1: first hardening pass for one target stage
- Round 2: follow-up pass after user feedback and observed behavior changes
- Round 3: final confirmation pass before calling that stage production-ready

If the stage is still unstable after Round 3, it is **not production ready**. Start a new evaluation cycle explicitly instead of silently extending the original one.

### 1. Plan To Production First

Before creating or editing any evaluation file, define the production target:

- what real behavior must change
- what failure mode must be prevented in production
- what exact stage, node, or prompt contract is under test
- what would count as production-safe behavior, not just demo-safe behavior

Write this production target into the relevant evaluation log before building the dataset.

The plan written into the evaluation log must include:
- target stage for this round
- round number (`1`, `2`, or `3`)
- what this round must prove before stopping
- what user-facing behavior changes will be surfaced after the round

Do not create a plan with more than 3 stages or 3 rounds in the same production-ready sequence.

Minimum planning questions:
- What production behavior are we trying to lock?
- What regression would hurt real students if this failed?
- What behavior should become stricter, softer, or more explicit?
- What should stay unchanged?

### 2. Create Or Update The Evaluation Audit Log

Before writing any JSONL attacks, update the canonical log in the vault `sources\docs\evaluation\` tree.

The log must include:
- architecture or seam being tested
- attack vectors
- targeted failure states
- expected extractor behavior
- expected analyst or synthesis behavior
- production target from Step 1
- attack checklist

The log is the reasoning contract. The dataset is only the executable payload.

### 3. Talk To The User About Meaningful Behavior Changes

If the proposed patch may change student-facing behavior, escalation behavior, probe style, confidence behavior, or the harshness/softness of the counseling flow:

- summarize the intended behavior change to the user in plain language
- call out the tradeoff
- ask for the user's opinion on the behavior change before treating it as final production direction

Examples of changes that require user discussion:
- stricter contradiction handling
- more aggressive reality checks
- softer Dreamer handling
- less tolerant compliance detection
- more deterministic probe composition
- more frequent or less frequent web research

This is not permission to stop progress. Build the draft, but do not silently lock major behavior shifts as the new production standard without surfacing them to the user.

### 4. Build The JSONL Attack Dataset

Add or update the dataset in `eval/`, usually:

- `eval/<graph>_attack.jsonl`

Each row should inject:
- the target stage
- the required prior profiles
- the stage conversation queue
- the semantic condition designed to break the graph

Keep attacks concrete and production-facing. Prefer realistic Vietnamese student cases over abstract toy prompts.

### 5. Run The Replay Pipeline

Run from repo root after activating the venv:

```powershell
venv\Scripts\activate
python eval/run_eval.py --mode multi --file eval/<target_attack>.jsonl --graph <target_graph>
```

Default regression mode is `multi` unless you specifically need a shared-thread replay.

### 6. Audit The Traces

Read the generated `traces/run_*.json` files. Do not treat exit code `0` as success by itself.

Check:
- did the graph run successfully
- did the extractor hold the right confidence boundaries
- did the analyst or synthesizer use the contradiction correctly
- did the final `PROBE:` survive
- did retrieval happen when required
- did user-facing behavior change in the intended direction

### 7. Patch And Re-Run

If the run fails:
- patch prompts, graph logic, or deterministic guards
- update the evaluation log
- re-run the same dataset

Repeat until the traces match the production target, not merely until the graph stops crashing.

### 8. Close The Loop With The User

After a meaningful draft works:
- summarize what changed
- report what passed and what still looks risky
- deliver the updated evaluation log for the finished stage
- ask the user for their opinion on any material behavior shift from Step 3
- stop the run there before starting the next stage or next round

This is required when the hardened behavior could alter the product's tone, aggressiveness, pacing, or trust model.

### 9. Record The Result

When the cycle is complete:
- update the stage-specific evaluation log
- update `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\context\docs\CURRENT_CONTEXT.md`
- update `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\DEV_LOG.md` if the decision should persist
- mirror the same dev-log entry into `D:\ANHDUC\Path_finder\logs\DEV_LOG.md`
- update canonical architecture or state docs in the vault if contracts changed

Production-ready requires all 3 rounds to be complete for the target stage:
- Round 1 complete and reviewed with the user
- Round 2 complete and reviewed with the user
- Round 3 complete and reviewed with the user

Do not call a stage production-ready after a single successful replay.

---

## Runner Requirements

- Run from repo root: `D:/ANHDUC/Path_finder`
- Activate the existing virtual environment first:

```powershell
venv\Scripts\activate
```

- Make sure `.env` contains the keys required by the selected graph

---

## CLI

```powershell
python eval/run_eval.py --mode single --file eval/purpose_attack.jsonl --graph purpose
python eval/run_eval.py --mode multi --file eval/purpose_attack.jsonl --graph purpose
python eval/run_eval.py --mode multi --file eval/thinking_attack_v2.jsonl --graph thinking --workers 4
```

---

## Arguments

- `--mode single|multi`
  - `single`: one shared `thread_id` for the whole dataset, inputs run sequentially
  - `multi`: one `thread_id` per input, inputs run concurrently
- `--file <jsonl_path>`
  - must point to a `.jsonl` file inside `eval/`
- `--graph <graph_name>`
  - canonical names: `thinking`, `purpose`, `goals`, `job`, `major`, `uni`, `output`, `orchestrator`
  - supported aliases: `thinking_graph`, `purpose_graph`, `goals_graph`, `job_graph`, `major_graph`, `uni_graph`, `university`, `output_graph`, `input_orchestrator`
- `--workers <int>`
  - optional, only relevant for `multi`
  - defaults to `min(8, number_of_inputs)`

---

## Input Shape

Each JSONL line is one independent input object.

The runner starts from `backend.data.state.DEFAULT_STATE`, then overlays each JSON object onto that state.

Normalization rules:

- if the target graph queue is missing but the row contains exactly one conversation queue, that queue is mirrored into the target queue
- if the row has `messages` only and the target graph is stage-specific, `messages` is mirrored into the stage queue
- if `stage.current_stage` is missing, the runner sets it from the selected graph

Prefer explicit stage queues in datasets:

- `thinking_style_message`
- `purpose_message`
- `goals_message`
- `job_message`
- `major_message`
- `uni_message`

---

## Trace Output

Trace files are written to:

```text
eval/threads/<thread_id>/traces/run_0001.json
```

Single mode:
- one `thread_id` for the entire dataset
- multiple trace files under the same thread directory

Multi mode:
- one `thread_id` per input row
- one trace file in each thread directory

Each trace JSON includes:
- `input`
- `output`
- `thread_id`
- `timestamp`
- `graph_name`
- `run_index`
- `graph_key`
- `graph_module`
- `input_file`
- `mode`
- `status`
- `normalized_input`
- `error_traceback` on failures

---

## Output Semantics

- `output` stores the full graph result state serialized into JSON-friendly data
- LangChain messages are serialized as objects with `type`, `content`, and any available metadata
- failures still produce a trace file with `status: "error"` and an error payload in `output`

---

## Completion Rule

An evaluation task is not done when:
- the dataset exists
- the command ran
- the graph returned `ok`

It is done when:
- the production target was written down first
- the round plan stayed within the 3-round cap
- traces were audited
- exactly one stage was finished in the run
- the canonical log was updated
- the updated log was handed to the user after the run
- meaningful behavior changes were surfaced to the user
- a user conversation happened before the next round started
- context docs were refreshed
