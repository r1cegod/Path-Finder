# CHALLENGE: Build context_compiler()

## Status: COMPLETE

`context_compiler()` in [output_graph.py](backend/output_graph.py) is implemented.
It delegates fully to `build_compiler_prompt(state)` in [output.py](backend/data/prompts/output.py).

This document is preserved as a reference for the decision logic.

---

## What Was Built

`context_compiler()` — a **pure Python decision tree** that reads state signals
and decides what prompt blocks the output LLM gets.

No LLM in this node. Just `if/elif/else`. This is the brain of the output compiler.

## The Architecture

```
  input_orchestrator                     output_graph
  ┌──────────────┐                ┌────────────────────────┐
  │ input_parser  │──► state ──►  │  context_compiler      │
  │ stage_manager │    signals    │  (Python decision tree) │
  │ counter_mgr   │               │         │               │
  └──────────────┘                │         ▼               │
                                  │  build_compiler_prompt() │
                                  │         │               │
                                  │         ▼               │
                                  │  output_compiler (LLM)  │
                                  └────────────────────────┘
```

## INPUTS (state signals read by build_compiler_prompt)

```python
state["bypass_stage"]              # bool — skip all stage logic?
state["escalation_pending"]        # bool — session ending?
state["escalation_reason"]         # str
state["message_tag"]               # MessageTag or dict
  .message_type                    #   "true"|"vague"|"genuine_update"|"disengaged"
                                   #   |"troll"|"avoidance"|"compliance"
  .user_drill                      #   bool — this answer needs more depth this turn
  .user_drill_reason               #   str  — WHY depth needed (empty if user_drill=False)
  .response_tone                   #   "socratic"|"firm"|"redirect"
state["user_tag"]                  # UserTag or dict
  .parental_pressure               #   bool
  .parental_pressure_reasoning     #   str (reasoning lock — written every turn)
  .burnout_risk                    #   bool
  .burnout_risk_reasoning          #   str
  .urgency                         #   bool
  .urgency_reasoning               #   str
  .core_tension                    #   bool
  .core_tension_reasoning          #   str
  .self_authorship                 #   str (free-form reasoning, empty = no signal yet)
  .compliance_reasoning            #   str
  .disengagement_reasoning         #   str
  .avoidance_reasoning             #   str
state["stage"]                     # StageCheck or dict
  .current_stage                   #   "thinking"|"purpose"|...|"path"
  .stage_related                   #   list[str]
state["compliance_turns"]          # int — managed by counter_manager
state["disengagement_turns"]       # int — managed by counter_manager
state["avoidance_turns"]           # int — managed by counter_manager
state["reality_gap"]               # bool
state["reality_gap_reasoning"]     # str
state["profile_summary"]           # ProfileSummary or dict
  .thinking / .purpose / ...       #   str (summary text per stage)
state[current_stage]               # e.g. state["purpose"] → PurposeProfile or None
```

## OUTPUT

```python
return {"compiler_prompt": str}  # assembled system prompt string
```

## THE DECISIONS

### Decision 1: compliance_level

```
compliance_turns → compliance_level mapping:
┌──────────────────────┬───────────────────┐
│ compliance_turns 0-3 │ None (too early)  │
│ compliance_turns 4-5 │ "low"             │
│ compliance_turns 6-7 │ "medium"          │
│ compliance_turns 8   │ "high"            │
│ compliance_turns 9+  │ "critical"        │
└──────────────────────┴───────────────────┘
BUT: if disengagement_turns >= 3 → compliance_level = None (suppressed)
```

### Decision 2: disengaged mode

```
disengagement_turns >= 3 → disengaged = True
  This GATES several things:
  ├─ user_drill is FORCED False (don't drill disengaged student)
  ├─ compliance_level is FORCED None (don't probe compliance)
  ├─ DISENGAGEMENT_BLOCK gets injected (MODE)
  └─ Most USER blocks suppressed (no core_tension, no parental_pressure, no self_authorship)
```

### Decision 3: profile_summary assembly

```
Read state["profile_summary"] → extract summaries for stage.stage_related stages.
Also: check what fields in the current stage's Profile are still empty.
That determines "fields_needed" for STAGE_PROGRESS_BLOCK.
```

### Decision 4: stage_status

```
For the current stage profile (e.g. PurposeProfile):
  - Count how many FieldEntry fields have confidence > 0
  - vs total FieldEntry fields
  → "2/6 fields extracted" or "not started"
```

### Decision 5: escalation routing

```
state["escalation_pending"] == True → CASE C
  CASE C SHORT-CIRCUITS everything. No stage, no user, no mode.
  The LLM writes a goodbye message and the session ends.
```

## THE DECISION TREE (visual)

```
build_compiler_prompt(state)
│
├─ escalation_pending == True?
│  └─ YES → CASE C
│          ESCALATION_BLOCK + static tail → DONE
│
├─ bypass_stage == True?
│  └─ YES → CASE A
│          BYPASS_BLOCK + static tail → DONE
│
└─ CASE B: Normal with stage
   │
   ├─ STAGE blocks (always)
   │  STAGE_CONTEXT + PROFILE_CONTEXT (if summary) + STAGE_PROGRESS
   │
   ├─ MODE block (mutually exclusive, priority order)
   │  ├─ disengaged?       → DISENGAGEMENT_BLOCK
   │  ├─ genuine_update?   → CELEBRATE_BLOCK
   │  ├─ tone=="firm"?     → FIRM_BLOCK
   │  ├─ tone=="redirect"? → REDIRECT_BLOCK
   │  └─ (else: socratic — no special MODE block)
   │
   └─ USER blocks (additive, 0-N can stack)
      ├─ user_drill AND NOT disengaged   → USER_DRILL_BLOCK
      ├─ active constraints > 0          → STAGE_DRILL_BLOCK
      ├─ compliance_level is set         → COMPLIANCE_PROBE_BLOCK
      ├─ avoidance_turns >= 3            → AVOIDANCE_BLOCK
      ├─ reality_gap                     → REALITY_GAP_BLOCK
      ├─ core_tension AND NOT disengaged → CORE_TENSION_BLOCK
      ├─ parental_pressure AND NOT dis.  → PARENTAL_PRESSURE_BLOCK
      ├─ self_authorship AND NOT dis.    → SELF_AUTHORSHIP_BLOCK
      ├─ burnout_risk                    → BURNOUT_BLOCK
      └─ urgency                         → URGENCY_BLOCK
```

## Files

| File | Purpose |
|------|---------|
| [output_graph.py](backend/output_graph.py) | context_compiler + output_compiler nodes |
| [output.py](backend/data/prompts/output.py) | All blocks + build_compiler_prompt() |
| [state.py](backend/data/state.py) | PathFinderState fields, profile models |
| [state_architecture.md](state_architecture.md) | Which node writes which field |
