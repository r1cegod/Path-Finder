# Sub-Orchestrator Flow And Round 3 Report

Last updated: 2026-04-10

> **TL;DR**: The sub-orchestrator lane now has a dedicated focus-eval workflow, bespoke prompt family, and a cleaner periodic-refresh policy. Round 3 passed for both `summarizer` and `worker`, which makes this lane production-ready at its own focus-eval seam, but not a substitute for broader full-system eval.

## What Changed

- Replaced the old thin shared sub-orchestrator templates with bespoke per-field prompts for:
  - summary workers
  - bool reasoning workers
  - text reasoning workers
- Added a dedicated focus-eval runner that bypasses the main orchestrator:
  - `eval/run_sub_orchestrator_focus_eval.py`
- Added a dedicated state normalizer for this eval seam:
  - `backend/sub_orchestrator_focus_eval.py`
- Added focused datasets for both families:
  - `eval/sub_orchestrator_summarizer_focus.jsonl`
  - `eval/sub_orchestrator_worker_focus.jsonl`
- Tightened periodic worker selection so low-signal pattern workers do not fire just because `turn_count % 5 == 0`
- Tightened summary refresh ownership so low-signal side summaries do not spill into unrelated fields
- Added deterministic text sanitation for odd mixed-script noise in generated outputs

## New Pieces

- `summarizer` focus graph
  - Runs `limit_check -> summary chain -> merge_summaries`
  - Used only for focused eval and trace audit

- `worker` focus graph
  - Runs `router -> selected workers -> merge`
  - Used only for focused eval and trace audit

- Full production sub-orchestrator
  - Still runs `limit_check -> summarizer if needed -> router -> workers -> merge`
  - Still returns:
    - `user_tag`
    - `user_tag_summaries`
    - `RemoveMessage(...)` updates for `routing_memory`

## Whole Flow

```text
main orchestrator
  │
  └──► sub_orchestrator_node
         │
         ├──► limit_check
         │      ├── under budget -> router
         │      └── over budget  -> summarizer chain
         │
         ├──► summary_parental_pressure
         ├──► summary_burnout_risk
         ├──► summary_urgency
         ├──► summary_core_tension
         ├──► summary_reality_gap
         ├──► summary_self_authorship
         ├──► summary_compliance
         ├──► summary_disengagement
         ├──► summary_avoidance
         ├──► summary_vague
         │
         ├──► merge_summaries
         │
         ├──► router
         │      └── selects only the fields that should actually refresh now
         │
         ├──► bool workers
         │      ├── parental_pressure
         │      ├── burnout_risk
         │      ├── urgency
         │      ├── core_tension
         │      └── reality_gap
         │
         ├──► text workers
         │      ├── self_authorship
         │      ├── compliance
         │      ├── disengagement
         │      ├── avoidance
         │      └── vague
         │
         └──► merge
                ├── writes final user_tag
                ├── keeps updated user_tag_summaries
                └── returns RemoveMessage updates for routing_memory
```

## Why The Flow Changed

- Round 1 showed that the lane could run directly, but it was too eager to refresh weak side fields.
- Round 2 reduced drift by changing:
  - when low-signal workers fire
  - when low-signal summaries refresh
- Round 3 added a small deterministic cleanup step for generated text noise and confirmed the stabilized flow.

## Evaluation Rounds

### Round 1
- Proved the new focus-eval seam worked.
- Exposed:
  - nested JSON-in-string output bug
  - side-field drift
  - language/noise instability

### Round 2
- Reduced false positives by:
  - tightening prompts
  - narrowing periodic worker refresh
  - narrowing summary ownership

### Round 3
- Added small deterministic text cleanup
- Re-ran the same focused datasets
- Confirmed the cleaned selection policy and summary ownership hold without reintroducing Round 1 drift

## Round 3 Commands

```powershell
python -m py_compile backend/sub_orchestrator_graph.py test_sub_orchestrator_graph_contract.py backend/data/prompts/sub_orchestrator.py backend/sub_orchestrator_focus_eval.py eval/run_sub_orchestrator_focus_eval.py
python -m unittest test_sub_orchestrator_graph_contract.py test_sub_orchestrator_focus_eval_contract.py
venv\Scripts\python eval/run_sub_orchestrator_focus_eval.py --target summarizer --file eval/sub_orchestrator_summarizer_focus.jsonl --mode single
venv\Scripts\python eval/run_sub_orchestrator_focus_eval.py --target worker --file eval/sub_orchestrator_worker_focus.jsonl --mode single
```

## Round 3 Trace Sets

- Summarizer thread: `c7325bac-e107-4e12-92d5-56cf901ac18f`
- Worker thread: `339e695d-3545-4f02-adca-e5520c2f32e9`

## Round 3 Verdict

- `summarizer`: pass
- `worker`: pass
- production-ready claim:
  - yes, at the dedicated sub-orchestrator focus-eval seam
  - no, not as a replacement for broader full-system evaluation

## Practical Takeaways

- The lane is now much more conservative about side-pattern inference.
- `self_authorship` still refreshes broadly because it is useful as a standing read on agency.
- Low-signal fields now need either:
  - active trigger evidence
  - or an already-established prior signal
- `RemoveMessage(...)` remains the right deletion mechanism for `routing_memory`.
- The main `messages` lane now uses the same deletion mechanism separately, with a 2k pre-orchestrator window that preserves the latest user turn.

## Key Files

- `backend/data/prompts/sub_orchestrator.py`
- `backend/sub_orchestrator_graph.py`
- `backend/sub_orchestrator_focus_eval.py`
- `eval/run_sub_orchestrator_focus_eval.py`
- `eval/sub_orchestrator_summarizer_focus.jsonl`
- `eval/sub_orchestrator_worker_focus.jsonl`
- `test_sub_orchestrator_graph_contract.py`
- `test_sub_orchestrator_focus_eval_contract.py`
