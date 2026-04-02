# PathFinder State Architecture

Single source of truth for every field in `PathFinderState`.
Updated by the architect agent after each approved change.

---

## Signal Flow Overview

```
User message
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  INPUT ORCHESTRATOR (orchestrator_graph.py)                   │
│                                                               │
│  check_node ──► summarizer (conditional) ──► input_parser     │
│                                                │              │
│                                    WRITES:     │              │
│                                    message_tag ◄──── LLM      │
│                                    user_tag                    │
│                                    bypass_stage               │
│                                    user_tag + reasoning       │
│                                    stage (partial)            │
│                                                │              │
│                                                ▼              │
│                                          stage_manager        │
│                                    WRITES:     │              │
│                                    stage (full)│              │
│                                    contradict_count           │
│                                    rebound_count              │
│                                                │              │
│                                                ▼              │
│                                         counter_manager       │
│                                    WRITES:                    │
│                                    troll_warnings             │
│                                    compliance_turns           │
│                                    disengagement_turns        │
│                                    avoidance_turns            │
│                                    turn_count                 │
│                                    trigger_window             │
│                                    escalation (if threshold)  │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE AGENTS (per-stage subgraph)                           │
│  scoring_node → analyst_node                                  │
│                                                               │
│  WRITES: {stage}Profile, stage_reasoning.{stage}            │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  OUTPUT COMPILER (output_graph.py)                           │
│                                                               │
│  context_compiler: reads all signals → builds compiler_prompt │
│  output_compiler:  LLM generates response from prompt        │
│                                                               │
│  READS: message_tag, user_tag, stage, all counters,          │
│         escalation_pending, stage_reasoning                  │
│  WRITES: compiler_prompt, messages (final response)          │
└─────────────────────────────────────────────────────────────┘

```

---

## Field Reference

### LAYER 1: CONVERSATION

| Field | Type | Writer | Reader | Lifecycle |
|---|---|---|---|---|
| `messages` | `Annotated[list, add_messages]` | All nodes (append) | All nodes | Grows, trimmed by summarizer |
| `summary` | `str` | summarizer_node | input_parser, summarizer | Grows (compressed history) |
| `stage_reasoning` | `StageReasoning` | Each stage analyst_node (own slot) | output compiler (PROFILE_CONTEXT_BLOCK) | Grows per stage; each turn analyst overwrites its slot |
| `{stage}_message` | `Annotated[list, add_messages]` | input_parser tagger + output_compiler tagger | Stage agent only | Persistent domain-specific memory bank of both student and assistant turns. Escapes global summarizer. |

### LAYER 2: ROUTING

| Field | Type | Writer | Reader | Lifecycle | Exit |
|---|---|---|---|---|---|
| `stage` | `StageCheck` | input_parser (partial), stage_manager (full) | stage_manager, counter_manager, output compiler | Updated each turn | N/A |
| `stage.current_stage` | `str` | stage_manager | All downstream | Advances on profile.done | N/A |
| `stage.stage_related` | `list[str]` | input_parser (LLM) | stage_manager | Per-turn | N/A |
| `stage.forced_stage` | `str` | input_parser (LLM) | stage_manager | Per-turn, clears after use | Clears to "" |
| `stage.rebound` | `bool` | input_parser (LLM) | stage_manager | Per-turn | N/A |
| `stage.contradict` | `bool` | stage_manager | counter_manager, output compiler | Per-turn | N/A |
| `stage.contradict_target` | `list[str]` | stage_manager | output compiler | Per-turn | N/A |
| `bypass_stage` | `bool` | input_parser (LLM) | Graph router (skip stage agents) | Per-turn | N/A |

### LAYER 3: PROFILES

All profiles start `None`. Filled by their stage agent's `scoring_node`. Persist for the rest of the session.

| Profile | Type | Writer | Read by | Exit |
|---|---|---|---|---|
| `thinking` | `ThinkingProfile` | thinking scoring_node | major, uni agents | Stage advances |
| `purpose` | `PurposeProfile` | purpose scoring_node | goals, job agents | Stage advances |
| `goals` | `GoalsProfile` | goals scoring_node | job, major agents | Stage advances |
| `job` | `JobProfile` | job scoring_node | major, uni agents | Stage advances |
| `major` | `MajorProfile` | major scoring_node | uni agent | Stage advances |
| `university` | `UniProfile` | uni scoring_node | output compiler | Terminal stage |

<details>
<summary>Profile field reference (all stages)</summary>

#### thinking — ThinkingProfile
Stage 0. How user learns and operates.

| Field | Type | Values |
|---|---|---|
| `done` | `bool` | Scoring gate |
| `learning_mode` | `FieldEntry` | `"visual"` · `"hands-on"` · `"theoretical"` |
| `env_constraint` | `FieldEntry` | `"home"` · `"campus"` · `"flexible"` |
| `social_battery` | `FieldEntry` | `"solo"` · `"small-team"` · `"collaborative"` |
| `personality_type` | `FieldEntry` | `"analytical"` · `"creative"` · `"social"` · `"builder"` · `"leader"` |
| `brain_type` | `list[str]` | MI intelligence types scoring 80+. Written by frontend quiz, read by thinking scoring_node. e.g. `["logical", "kinesthetic"]` |
| `riasec_scores` | `list[str]` | Top 2-3 Holland Codes from frontend quiz. Written by frontend, read by job agent. e.g. `["Realistic", "Investigative"]` |

#### purpose — PurposeProfile
Stage 1. WHY they want anything.

| Field | Type | Values |
|---|---|---|
| `done` | `bool` | Scoring gate |
| `core_desire` | `FieldEntry` | `"wealth"` · `"impact"` · `"creative control"` · `"freedom from X"` |
| `work_relationship` | `FieldEntry` | `"calling"` · `"stepping stone"` · `"necessary evil"` |
| `ai_stance` | `FieldEntry` | `"fear"` · `"leverage"` · `"indifferent"` |
| `location_vision` | `FieldEntry` | `"remote"` · `"relocate to US"` · `"tied to hometown"` |
| `risk_philosophy` | `FieldEntry` | `"startup risk"` · `"corporate ladder"` · `"gov stability"` |
| `key_quote` | `FieldEntry` | Verbatim quote capturing their core essence |

#### goals — GoalsProfile
Stage 2. WHAT they want. Wraps two horizons.

**goals.long** (5-10 year): `income_target`, `autonomy_level`, `ownership_model`, `team_size`
**goals.short** (1-2 year): `skill_targets`, `portfolio_goal`, `credential_needed`

#### job — JobProfile
Stage 3. WHERE they land.

Fields: `role_category`, `company_stage`, `day_to_day`, `autonomy_level`

#### major — MajorProfile
Stage 4. HOW they get qualified.

Fields: `field`, `curriculum_style`, `required_skills_coverage`

</details>

### LAYER 4: SIGNALS

#### MessageTag (per-turn — overwritten every turn)

| Field | Type | Writer | Reader | Exit |
|---|---|---|---|---|
| `message_tag` | `MessageTag \| None` | input_parser (LLM) | counter_manager, output compiler | Overwritten next turn |
| `.message_type` | `str` | LLM | counter_manager (6 counters), output compiler | `"true"\|"vague"\|"troll"\|"genuine_update"\|"disengaged"\|"avoidance"\|"compliance"` |
| `.user_drill` | `bool` | LLM | output compiler (USER_DRILL_BLOCK) | Overwritten next turn |
| `.user_drill_reason` | `str` | LLM | output compiler (USER_DRILL_BLOCK) | Overwritten next turn |
| `.response_tone` | `str` | LLM | output compiler (MODE selection) | `"socratic"\|"firm"\|"redirect"` |

#### UserTag (persistent — reasoning lock, ALL fields written EVERY turn)

| Field | Type | Writer | Reader | Exit |
|---|---|---|---|---|
| `user_tag` | `UserTag \| None` | input_parser (LLM) | output compiler | N/A |
| `.parental_pressure` | `bool` | LLM | output compiler (block gate) | `False` when resolved |
| `.parental_pressure_reasoning` | `str` | LLM | output compiler (block content) | `""` when resolved |
| `.burnout_risk` | `bool` | LLM | output compiler (block gate) | `False` when resolved |
| `.burnout_risk_reasoning` | `str` | LLM | output compiler (block content) | `""` when resolved |
| `.urgency` | `bool` | LLM | output compiler (block gate) | `False` when resolved |
| `.urgency_reasoning` | `str` | LLM | output compiler (block content) | `""` when resolved |
| `.core_tension` | `bool` | LLM | output compiler (block gate) | `False` when resolved |
| `.core_tension_reasoning` | `str` | LLM | output compiler (block content) | `""` when resolved |
| `.self_authorship` | `str` | LLM | output compiler (block content) | `""` when self-authored |
| `.reality_gap` | `bool` | LLM | output compiler (block gate) | `False` when resolved |
| `.reality_gap_reasoning` | `str` | LLM | output compiler (block content) | `""` when resolved |
| `.compliance_reasoning` | `str` | LLM | output compiler (COMPLIANCE_BLOCK) | `""` when genuine |
| `.disengagement_reasoning` | `str` | LLM | output compiler (DISENGAGEMENT_BLOCK) | `""` when re-engaged |
| `.avoidance_reasoning` | `str` | LLM | output compiler (AVOIDANCE_BLOCK) | `""` when addressed |
| `.vague_reasoning` | `str` | LLM | output compiler (VAGUE_BLOCK) | `""` when concrete |

### LAYER 5: COUNTERS (managed by Python, not LLM)

| Field | Type | Writer | Trigger | Decay | Warn | Escalate |
|---|---|---|---|---|---|---|
| `troll_warnings` | `int` | counter_manager | `message_type=="troll"` | max(0,-1) | — | direct (window) |
| `compliance_turns` | `int` | counter_manager | `message_type=="compliance"` | max(0,-1) | — | window forces to 9, threshold=10 |
| `disengagement_turns` | `int` | counter_manager | `message_type=="disengaged"` | max(0,-1) | >= 3 | >= 4 |
| `avoidance_turns` | `int` | counter_manager | `message_type=="avoidance"` | max(0,-1) | >= 3 | >= 4 |
| `contradict_count` | `int` | stage_manager | `stage.contradict==True` | max(0,-1) | — | direct (window) |
| `rebound_count` | `int` | stage_manager | `stage.rebound==True` | max(0,-1) | — | direct (window) |
| `turn_count` | `int` | counter_manager | Every turn | Monotonic +1 | — | Window check at %10 |
| `trigger_window` | `dict` | counter_manager | Per-counter per turn | Resets every 10 turns | — | Any >= 5/10 → escalate |

### LAYER 6: SYSTEM

| Field | Type | Writer | Reader | Lifecycle | Exit |
|---|---|---|---|---|---|
| `path_debate_ready` | `bool` | stage_manager | output compiler | Per-turn | N/A |
| `stage_transitioned` | `bool` | stage_manager | output compiler | One-turn pulse | Resets next turn |
| `compiler_prompt` | `str` | context_compiler (Python) | output_compiler (LLM) | Per-turn | N/A |
| `escalation_pending` | `bool` | stage_manager, counter_manager | output compiler | Sticky once True | Session ends |
| `escalation_reason` | `str` | stage_manager, counter_manager | output compiler | Set when escalation triggers | Read once |
| `limit_hit` | `bool` | check_node | Graph router | Per-turn | N/A |
| `verdict` | `dict \| None` | Verdict check | output compiler, path_agent | Written once | N/A |

---

## Counter Decision Table

```
COUNTER              TRIGGER                    DECAY        PROMPT TRIGGER        ESCALATION
─────────────────    ────────────────────────   ──────────   ──────────────────    ─────────────────
troll_warnings       message_type="troll"       max(0,-1)    FIRM_BLOCK            window >= 5/10
compliance_turns     message_type="compliance"  max(0,-1)    COMPLIANCE_PROBE      window → force 9
                                                             (technique by level)  threshold = 10
disengagement_turns  message_type="disengaged"  max(0,-1)    >= 3: WARNING BLOCK   >= 4: escalate
avoidance_turns      message_type="avoidance"   max(0,-1)    >= 3: WARNING BLOCK   >= 4: escalate
contradict_count     stage.contradict=True      max(0,-1)    (stage routing)       window >= 5/10
rebound_count        stage.rebound=True         max(0,-1)    (stage routing)       window >= 5/10
trigger_window.*     per-counter per turn       resets/10    —                     any >= 5 (50%)
```

---

## Signal Relationships

```
parental_pressure ──────────────────────────┐
  (root cause)                              │
     │                                      ▼
     ├──► self_authorship ≠ ""             core_tension
     │    (symptom: whose voice?)           (the conflict)
     │
     ├──► message_type = "compliance"
     │    (per-turn evidence → counter)
     │
     └──► compliance_reasoning
          (persistent context for output)

disengagement_turns >= 3
     │
     └──► DISENGAGEMENT_BLOCK (warning)
          disengagement_turns >= 4
          └──► escalation_pending = True

avoidance_turns >= 3
     │
     └──► AVOIDANCE_BLOCK (warning)
          avoidance_turns >= 4
          └──► escalation_pending = True
```

---

## Rules for Adding New Fields

1. **Every field must have a WRITER, READER, and EXIT condition**
2. **No field should only go up** — if it increments, it must also decay or have a clear exit
3. **LLM classifies, Python counts** — LLM outputs booleans/strings, Python nodes manage counters
4. **Per-turn vs persistent must be explicit** — document which type in the field comment
5. **Signal overlap must be documented** — if two fields detect similar things, document the relationship
6. **Run new fields through the architect agent** before adding to state
7. **Reasoning lock** — UserTag fields are written ALL every turn. No field goes stale.
