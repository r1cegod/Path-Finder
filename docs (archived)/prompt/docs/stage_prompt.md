# Stage Prompt Audit Guide

Reference for writing and auditing every stage agent prompt in PathFinder.
Updated as new patterns are discovered.

---

## What a Stage Agent Actually Does

```
student message
      │
      ▼
 confident_node  ── reads {stage}_message + current profile
      │              writes structured FieldEntry values back to state
      ▼
 analyst_node    ── reads {stage}_message + current profile + stage_reasoning
      │              writes structured REASONING to stage_reasoning.{stage}
      ▼
 output compiler ── reads stage_reasoning.{stage} via PROFILE_CONTEXT_BLOCK
                     generates the student-facing Vietnamese response
```

**The Stage Agent Mental Model:**
A stage agent is just *one lobe* of PathFinder's brain dedicated exclusively to internal processing for a single profile. Its entire prompt architecture must focus zero percent on "how to reply to the user" and one hundred percent on "how to reason about this specific domain." 

The analyst node is NOT a chatbot. It produces internal English reasoning. It detects contradictions, applies domain heuristics, and designs the next logical Socratic attack. The output compiler is the ONLY node accountable for tone, empathy, and generating the actual student-facing Vietnamese response. 

If a stage prompt contains instructions on *how to talk*, it is polluting the reasoning layer.

---

## Prompt Block Structure

### Drill prompt (analyst_node)

Every stage analyst prompt must have these blocks in this order:

```
<context>        runtime state I can read (injected via .format()) — FIRST so model has
                 state before reading its role. MUST include is_current_stage.
<identity>       who am I (NAMED), what I do NOT do
<architecture>   pipeline position, what my output feeds into
<scope>          fields I analyze — descriptions only, no enum literals
<instructions>   how to reason, step-by-step — classification rules live HERE
                 (merges what was formerly a separate <knowledge> block)
<guardrails>     what I must not do
<output_format>  free reasoning + suggestive questions + PROBE: anchor
```

### What belongs in each block

**`<identity>`**
Give the analyst a NAME (e.g., `name="Kai"`). GPT-mini responds better to a named
role than an abstract description. Include what it does NOT do (respond to student).

**`<instructions>`**
Step-by-step. Classification rules live here as numbered steps, NOT as a taxonomy block.
GPT-mini follows explicit numbered steps more reliably than a separate `<knowledge>`
taxonomy. Structure: steps 1–N covering:
(1) **Read context & The Priors Cross-Check**: map how prior stage fields clash with current fields to find structural tension.
(2) **Classify information type**: behavioral vs self-report vs compliance.
(3) **The Verification Squeeze**: explicitly design a trade-off/stress-test to push unverified self-reports over the 0.7 threshold.
(4) **Write analysis**.

Anti-patterns inside instructions:
- No specific examples ("nuôi bố mẹ → external driver") — define the CLASS instead
- No numeric ceilings or floors — confident_node handles scoring
- No verbatim question suggestions

**`<guardrails>`**
Constraints on analyst behavior. What it must never do. No task steps here.

**`<output_format>`**
Free-form reasoning + suggestive questions + a single required anchor. This is the
primary deliverable of the prompt. Rigid sections are too limiting — the analyst
writes what is relevant, guided by the questions, and closes with PROBE:.

---

## The Reasoning Output Contract

All stage analysts produce free-form reasoning ending with a single structured anchor:

```
[free-form reasoning about what this turn revealed]

Address whichever of these questions apply:
- What information type is the student expressing?
- Is there a conflict, test-behavior mismatch, or compliance pattern?
- What is blocked and why (cross-field dependency)?
- What should be probed next?
- Any downstream signal for later stages?

If is_current_stage is True, end with:
PROBE: [field_name] — [scenario/probe type, 1 sentence]

If is_current_stage is False, end with:
PROBE: NONE (passive analysis only)
```

The questions are SUGGESTIVE — the analyst answers those that are relevant to this turn.
There is no requirement to address all of them or to use section headers.

"blocked: [reason]" is still the correct language when a field is structurally blocked
(not "no signal"). Use it in the reasoning narrative, not a separate FIELD STATUS block.

Upstream profile priors (e.g. ThinkingProfile personality_type) appear in the
free-form reasoning when they change the interpretation of evidence.

Rules baked into every output_format block:
- English only, third person, never address the student
- PROBE: is the ONLY required structured output — field name + scenario type, 1 sentence
- If nothing new this turn, say so and carry the same PROBE: forward

### Probe Ownership

In the current architecture, an actionable `PROBE:` belongs ONLY to the active stage.

- If `is_current_stage=True`, the analyst must hand the output compiler one concrete next attack.
- If `is_current_stage=False`, the analyst is in passive-analysis mode only and must end with `PROBE: NONE (passive analysis only)`.
- Reason: only the active stage is allowed to drive the next student-facing Socratic squeeze. Non-current stages can add interpretation, but they must not compete for control of the next turn.

When a graph uses structured analyst outputs plus Python composition:
- the LLM should return normal analysis in `*_summary`
- the LLM should return probe metadata in dedicated fields such as `probe_field`, `probe_tension`, and `probe_instruction`
- Python may deterministically compose the final `PROBE:` line from those fields
- any cleanup of leaked legacy `PROBE:` text inside `*_summary` is defensive normalization, not the primary contract

---

## The Verification Loop (Strict Scoring & Stress-Testing)

Stage agents must actively hunt for the truth, not passively accept self-reports. This requires a tight, adversarial loop between the Extractor and the Analyst:

1. **The Verification Cap (Extractor):** 
   The `confident_node` must **NEVER** score a self-report > 0.6. A mere statement of preference is an unverified claim. A field only crosses the 0.7 threshold if the student actively chooses it over a competing desire or defends it structurally.
2. **The Verification Squeeze (Analyst):** 
   Because the Extractor caps self-reports at 0.6, the `analyst_node` MUST design a stress-test to push the student over that threshold. If a field is unverified, the analyst's `PROBE:` must present a hard trade-off, play devil's advocate, or force a zero-sum sacrifice. Do not just ask "why."
3. **The Priors Cross-Check (Analyst):** 
   The analyst leverages data from *completed previous stages* injected into `<context>` as ammunition. It cross-checks the student's current claims against their verified priors (e.g., cross-checking a "founder" goal against a "stability" risk philosophy) to generate structural tension for the drill.
4. **Python Owns Hard Thresholds:** 
   If a stage has deterministic prerequisites for high confidence (for example, a minimum number of human turns before any field may exceed `0.6`), enforce that in Python inside the `confident_node` before writing the profile back to state. Prompt wording alone is not enough when the threshold is structural.

---

## The Red-Team Evaluation Workflow (Automated Pipeline)

Agent prompts are not considered "done" until they survive a structured, adversarial attack. Manual testing via LangGraph Studio is insufficient for edge cases.

The official evaluation workflow now lives in:
- `eval/HOW_TO_USE.md`

That file is the single source of truth for:
- production-first evaluation planning
- evaluation log creation rules
- JSONL dataset workflow
- replay commands
- trace auditing
- the rule to surface meaningful behavior changes to the user and ask for their opinion before locking them as production direction

---

### Confident prompt (confident_node)

Every stage extractor prompt must have these blocks in this order:

```
<context>        current {stage}Profile state (injected via .format()) — FIRST
<identity>       NAMED extractor, what it does NOT do
<definitions>    fields to extract — two sections:
                   PROTECTED FIELDS: read-only (e.g. test-seeded), copy verbatim
                   EXTRACTABLE FIELDS: description + examples (not "exact values")
                   done gate lives here — not in drill prompt
<instructions>   numbered steps: read history → match category → score → handle special fields
<guardrails>     overwrite rules, fallback values, verbatim-only fields
<output_format>  output schema reference only (no free text)
```

**`<definitions>` — two sections:**
- Protected fields (if any): listed first, with VERBATIM copy rule
- Extractable fields: description explains what to look for; examples are the valid
  category labels (not strict enum strings — model should reason to them)
- `done` gate lives here only, with explicit field list and threshold

---

## Token Cap Enforcement

**Do NOT put token limits in the prompt.** LLMs don't reliably count tokens.

Hard enforcement is at the LLM object level in the graph file:

```python
# In {stage}_graph.py — analyst node only
analysis_llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=450).with_structured_output(ThinkingAnalysis)
#                                               ↑ hard wall
# 450 = ~400 content + ~50 JSON wrapper overhead
# confident_llm has no max_tokens — extractor output size is schema-bounded
```

---

## What Is Wrong-Layer

Things that look right but belong elsewhere:

| Found in prompt | Problem | Where it belongs |
|---|---|---|
| Verbatim Vietnamese question in `<knowledge>` | Analyst doesn't phrase questions | Output compiler |
| "probe type: X" in `<knowledge>` | Output guidance mixed into knowledge | Flows from NEXT PROBE naturally |
| Token count instruction in `<output_format>` | LLM ignores it | `max_tokens` on LLM object |
| Step-by-step task instructions in `<knowledge>` | Knowledge ≠ task list | `<guardrails>` or `<output_format>` |
| Prior stage data injected without explaining what it means | Analyst will ignore unknown fields | Add a `<test_data>` or prior section in `<context>` |

---

## Prior Stage Data Rules

When a stage analyst needs data from a completed prior stage:

1. Inject the profile object into `<context>` via `.format(prior_profile=...)`
2. Add a section in `<knowledge>` explaining what fields to use as priors and how they map
3. Label the injected field in `<context>` with an arrow comment:
   ```
   ThinkingProfile (Stage 0, complete): {thinking}
     ↑ use personality_type as prior for core_desire and risk_philosophy
   ```

Thinking stage has two special test-seeded fields:
- `brain_type` / `riasec_top` — written by frontend quiz, not conversation
- `confident_node` must preserve these verbatim (see `<test_data_contract>` in thinking.py)
- `analyst_node` uses them as priors with the same rules as any prior: test ≠ verdict

---

## Audit Checklist

Before shipping any stage prompt, verify:

```
[ ] <context> block is FIRST — model has state before reading its role
[ ] <identity> has a NAME (e.g., name="Kai") — not just a role description
[ ] <scope> uses descriptions of what each field captures — not enum string literals
[ ] No separate <knowledge> block — classification rules live in <instructions> as steps
[ ] <instructions> has NO verbatim questions, NO probe suggestions, NO numeric thresholds
[ ] <output_format> is free-form + suggestive questions, NOT rigid section headers
[ ] <output_format> has NO FIELD STATUS rows — current field state lives in {context}
[ ] <output_format> has NO token count instruction
[ ] PROBE: anchor ends the output — field name + scenario type, 1 sentence
[ ] Actionable PROBE only appears when `is_current_stage=True`; otherwise `PROBE: NONE (passive analysis only)`
[ ] done gate exists ONLY in confident_node <definitions> — not in drill prompt
[ ] max_tokens=450 set on analysis_llm in the graph file
[ ] confident_node: <context> is FIRST block
[ ] confident_node: <identity> has a NAME
[ ] confident_node: <definitions> has PROTECTED FIELDS section (if any read-only fields) before extractable fields
[ ] confident_node: extractable fields use "Examples:" not "Exact values:"
[ ] confident_node: done gate is in <definitions>, not in drill prompt
[ ] key_quote (if present) has explicit verbatim-only guardrail in confident_node
[ ] Prior stage data injected into <context> AND explained in <instructions> HOW TO USE step
```

---

## Stage Prompt Status

| Stage | Analyst prompt | Confident prompt | max_tokens set | Audited |
|-------|---------------|-----------------|----------------|---------|
| thinking (0) | yes | yes | yes | 2026-04-05 (S4 re-audit) |
| purpose (1)  | yes | yes | yes | 2026-04-05 (S4 re-audit) |
| goals (2)    | yes | yes | yes | 2026-04-05 (S4) |
| job (3)      | yes | yes | yes | 2026-04-05 (retrieval audit pass) |
| major (4)    | placeholder | placeholder | no | no |
| uni (5)      | placeholder | placeholder | no | no |

---

## Audit Log

Design decisions recorded as they were made. Each entry shows the decision,
the before state, the after state, and why it matters.

---

### 2026-03-30 — Session 1: thinking.py + purpose.py

**[A1] Analyst node ≠ chatbot node**
Stage agents originally ran: scoring → summarizer → chatbot. The chatbot wrote
Vietnamese responses into `{stage}_message`. The output compiler reads
`state["messages"]` (global) — never `{stage}_message`. Two LLM calls per turn,
one doing invisible work.

Decision: Remove chatbot node and summarizer from all 6 stage subgraphs. Stage agents
are analysts only. Output compiler is the sole student-facing response generator.

Before: `scoring_node → summarizer_node → chatbot_node`
After:  `scoring_node → analyst_node`

---

**[A2] Verbatim Vietnamese questions in `<knowledge>` are wrong-layer**
`<knowledge>` contained scenario bank entries like:
  `"Sau 8 tiếng làm nhóm, em cảm thấy..." → probe social_battery`
The analyst doesn't phrase questions. Output compiler does.

Decision: Remove all verbatim question text. `<knowledge>` contains probe TYPE labels
only. Output compiler decides actual phrasing.

Before: `social_battery: "Sau 8 tiếng làm project nhóm, em thấy được nạp năng lượng..."`
After:  probe type label only, e.g. `forced binary energy scenario after group work`

---

**[A3] Numeric thresholds don't belong in prompts**
`<knowledge>` had confidence ceilings: `"empty bucket words → ceiling 0.3"`.
LLMs don't reliably count or respect numeric thresholds in prompt text.
Scoring is confident_node's job, not the analyst's.

Decision: Remove all numeric thresholds from drill prompts. confident_node handles
scoring. Analyst recognizes information TYPES and flags them.

Before: `External obligation framing → ceiling 0.3; classify as external driver`
After:  `WHAT IS AN EXTERNAL DRIVER: a desire framed as obligation to others...`

---

**[A4] Knowledge = taxonomy of information types, not lookup table**
`<knowledge>` was a list of Vietnamese patterns with "you see X, do Y" rules.
This only handles known patterns — it doesn't teach the LLM to recognize NEW patterns.

Decision: Rewrite `<knowledge>` as definitions of information TYPES. Each entry answers
"what IS this type and what does its presence mean." LLM can then apply the definition
to any new pattern it encounters.

Before: `"Nuôi bố mẹ" framing → external driver; flag parental_pressure`
After:  `WHAT IS AN EXTERNAL DRIVER: a desire framed as obligation to others.
         An external driver tells you about the student's CONTEXT, not preference.`

---

**[A5] FIELD STATUS restates data the context already has**
The FIELD STATUS block in `<output_format>` listed all fields every turn:
  `learning_mode: prior: X | behavioral: Y`
But `{thinking}` in `<context>` already carries the current extracted state. The analyst
was reporting information the output compiler can read directly from state.

Decision: Remove FIELD STATUS entirely. Analyst output = CONFLICT/COMPLIANCE +
NEXT PROBE + NOTES. The analyst's value-add is what's NOT in the structured profile:
conflicts, compliance risks, and cross-field tensions.

Before: FIELD STATUS rows + CONFLICT + NEXT PROBE + NOTES
After:  CONFLICT/COMPLIANCE + NEXT PROBE + NOTES

---

**[A6] `prior:` in FIELD STATUS embedded ThinkingProfile into the format contract**
`core_desire: prior: [personality_type signal] | evidence: [...]`
ThinkingProfile is upstream context for reasoning — not a field being reported.
Baking it into FIELD STATUS made the format wrong for any stage without upstream data.

Decision: Upstream profile priors belong in NOTES when relevant to a specific
assessment. FIELD STATUS (while it existed) reported only conversational evidence.
Now that FIELD STATUS is removed, priors surface naturally in CONFLICT or NOTES.

Before: `core_desire: prior: social → obligation risk | evidence: ...`
After:  NOTES: `personality_type=social raises external-driver prior. Consistent.`

---

**[A7] Done gate belongs only in confident_node**
The drill prompt's `<scope>` had: `all must reach confidence > 0.7 before done=True`.
The analyst doesn't set done. It doesn't score. The done gate is a scoring rule.

Decision: Remove done gate from drill prompt entirely. It lives only in confident_node
`<definitions>`. Drill prompt's `<scope>` describes fields only.

Before: `Fields to analyze (all must reach confidence > 0.7 before done=True)`
After:  `Fields to analyze — understand what each captures:`

---

**[A8] Field values in drill prompt should be descriptions, not enum strings**
`<scope>` listed: `learning_mode: "visual" | "hands-on" | "theoretical"`
Enum strings are for the extractor (confident_node). The analyst needs to understand
WHAT TO LOOK FOR — not what string to match.

Decision: Drill prompt `<scope>` uses descriptions. Confident_node `<definitions>`
uses both description AND exact enum literals.

Before: `- learning_mode: "visual" | "hands-on" | "theoretical"`
After (drill): `- learning_mode: the mode of information intake that produces fastest
               uptake with least friction for this student`
After (confident): `- learning_mode: the mode of information intake...
                    Examples: "visual" | "hands-on" | "theoretical"`

---

### 2026-03-30 — Session 2: block order + output format rework

**[A9] Context block first — model has state before reading its role**
Block order was: identity → architecture → context → ...
GPT-mini benefits from having the injected runtime state (current profile, prior stage
data) loaded before it reads its role and task. When context comes first, the role
framing applies on top of already-loaded state.

Decision: Reorder all drill prompts to: context → identity → architecture → scope →
instructions → guardrails → output_format.

Before: `<identity>` first, `<context>` third
After:  `<context>` first, `<identity>` second

---

**[A10] Named identity — GPT-mini responds better to a persona than a role description**
identity block was: "You are PathFinder's Thinking Analyst (Stage 0)."
Anonymous role descriptions are weaker anchors than named personas for GPT-mini.
A name creates consistent role identity across a multi-turn conversation.

Decision: Add a name attribute to every stage identity.

Before: `<identity> You are PathFinder's Thinking Analyst (Stage 0). ...`
After:  `<identity name="Kai — PathFinder's Thinking Analyst"> ...`

---

**[A11] Knowledge block → Instructions (GPT-mini follows steps, not taxonomy)**
The `<knowledge>` block was a WHAT IS taxonomy — good for understanding but not
for execution. GPT-mini follows explicit numbered steps more reliably than
taxonomy-style classification rules. Moving the classification knowledge INTO numbered
steps in `<instructions>` gives the same definitions but as an action plan.

Decision: Remove `<knowledge>` as a separate block. Merge classification rules as
step content inside `<instructions>`. First steps = context + prior reading.
Later steps = information type classification + dependency check + probe selection.

Before: Separate `<knowledge>` block with WHAT IS taxonomy
After:  `<instructions>` step 1 = read priors, step 2/3 = classify information type,
        step 4 = identify unresolved field, step 5 = write analysis

---

**[A12] Output format: free reasoning + suggestive questions (rigid template removed)**
The CONFLICT/COMPLIANCE + NEXT PROBE + NOTES template forced the analyst into three
sections every turn, even when only one was relevant. The analyst was writing empty
or forced sections to satisfy the format.

Decision: Replace rigid template with free-form reasoning, guided by a set of suggestive
questions the analyst addresses if relevant, ending with a single required anchor: PROBE:

The suggestive questions cover the same concerns (information type, conflicts, blocking,
next probe, downstream signal) but don't require section headers or all-or-nothing answers.

Before:
```
CONFLICT/COMPLIANCE: [...]
NEXT PROBE: [field] — [type]
NOTES: [...]
```
After:
```
[free-form reasoning]
Address whichever apply:
- [suggestive questions]
PROBE: [field_name] — [type, 1 sentence]
```

---

**[A13] "Exact values" → "Examples" in confident prompts**
`<definitions>` said `Exact values: "visual" | ...` — implies strict lookup, which
primes the extractor to pattern-match rather than reason about what the student said.
"Examples" is more accurate: these are the valid category labels, but the model should
reason to them, not scan for them.

Before: `Exact values: "visual" | "hands-on" | "theoretical"`
After:  `Examples: "visual" | "hands-on" | "theoretical"`

---

### 2026-03-30 — Session 3: confident prompt structure

**[A14] Confident prompt block order: context first, named identity**
Confident prompts had `identity → context → ...`. Same rationale as [A9] for drill prompts:
model should have the current extracted state loaded before reading its role.
Named identity added for same reason as [A10].

Decision: Reorder to `context → identity(named) → definitions → instructions → guardrails → output_format`.

Before: `<identity> You are PathFinder's Thinking Extractor. …` (first block)
After:  `<context>` first, then `<identity name="Nova — …">`

---

**[A15] test_data_contract folded into definitions**
`<test_data_contract>` was a standalone block between `<context>` and `<definitions>`
in thinking's confident prompt. It describes read-only fields — that's definition content,
not a separate block type. Separating it added a 4th block with no structural justification.

Decision: Fold into `<definitions>` as a "PROTECTED FIELDS" section before extractable fields.
Shape: PROTECTED FIELDS (verbatim copy rule) → CONVERSATIONAL FIELDS (extract + score).

Before: standalone `<test_data_contract>` block
After:  `<definitions>` split into two labeled sections: PROTECTED FIELDS / CONVERSATIONAL FIELDS

---

**[A16] Purpose analyst reads message_tag instead of re-detecting compliance/vague**
Purpose analyst step 1 was re-classifying COMPLIANCE ANSWER, VAGUE ABSTRACTION,
and EXTERNAL DRIVER — all already classified by the orchestrator and available in
`message_tag` and `user_tag`. Duplicate detection means two LLMs making the same call
with different evidence sets. Orchestrator has the full turn context; analyst only has
what's in stage_reasoning + the message queue.

Decision: Inject `message_tag` into purpose analyst `<context>`. Step 1 reads the tag
and draws field implications (which fields are blocked/untrusted this turn).
Analyst-unique classification (UNVERIFIED CLAIM, VERIFIED SIGNAL) stays in step 2.

Before: step 1 = detect compliance/vague/external driver from scratch
After:  step 1 = read message_tag → field implications; step 2 = analyst-unique classification

---

**[A17] Stage Agents reason. Output Compiler responds.**
A stage agent is one lobe of the brain focused entirely on processing its domain. It doesn't
worry about tone, empathy, or language (Vietnamese). When prompt authors try to instruct
a stage agent on *how to talk*, they pollute the reasoning space with response-generation constraints.

Decision: The prompt design philosophy explicitly forbids any instructions related to 
"how to reply." All prompt logic must be 100% dedicated to domain heuristics, contradiction
detection, and formulating the logical Socratic attack.

Before: Chatbot instructions littered across stage nodes 
After: Clean, adversarial reasoning pipeline producing a `PROBE:`

---

**[A18] The Verification Cap (Strict 0.7 Guardrail) + The Verification Squeeze**
Confident nodes were treating student self-reports (e.g., "I want to be rich") as verified
truth, locking them at >0.7. This allowed students to pass stages without their goals being
reality-tested.

Decision: Enforce a strict `0.6` ceiling for any self-report. A field only crosses `0.7` if
the student chooses it over a competing desire or defends it against Socratic pushback.
To make this work, the Analyst prompt now requires a "Verification Squeeze": if a field is
an unverified self-report, the Analyst MUST design a stress-test (hard trade-off, devil's
advocate) rather than just asking "why."

Before: Self-reports could score >0.7. Analyst asked "why did you say that?"
After:  Self-reports cap at 0.6. Analyst forces a zero-sum trade-off to test the claim.

---

**[A19] The Cross-Check Logic (Priors as Stressors)**
A stage agent cannot view its fields in isolation. A powerful prompt uses data from completed
previous stages to actively generate structural tension. For example, Stage 2 (Goals) must
cross-check the student's *new* `long_term_goal` against their *already-locked*
`purpose.risk_philosophy` to hunt for a crash. Stage 4 (Major) must cross-check 
`thinking.learning_mode` against the major's reality.

Decision: Prior stage data injected into `<context>` is not passive reading material. It is
ammunition. The `<instructions>` block must explicitly define "The Priors Cross-Check" 
(e.g., The Horizon Squeeze, The Fit Test, The Modality Squeeze) so the analyst 
knows *exactly* which priors clash with which current fields.

Before: Priors were injected but the analyst wasn't told how they clash.
After: Priors are explicitly mapped in `<instructions>` to trigger structural crashes.

---

**[A20] Data Agents (Tools): Generalized Pipeline vs. Trigger Matrix**
The Stage 3 (Job) Agent uses a `search` tool. Initial designs proposed hardcoded triggers
(e.g., "If social_battery=solo and role=PM, search meeting load"). This scales poorly,
bloats the prompt, and causes GPT-mini to hallucinate or ignore rules.

Decision: Tool use must be governed by a generalized, sequential flowchart in `<instructions>`:
1. **The Baseline:** Identify student's most extreme constraints (friction points).
2. **The Query:** Formulate search targeting the intersection of the Job Role and the Friction Point (no generic averages).
3. **The Synthesis:** Compare Market Consensus vs Profile Prior.
4. **The Exception:** If student names an outlier execution strategy to beat the consensus, search the barrier to entry of that strategy, do not attack the ambition.

Before: "If X and Y, search Z." (brittle trigger matrix)
After:  "Find the friction point. Aim the search at the friction point. Test the consensus against the friction point." (generalized reasoning pipeline)

---

**[A21] Major Agent (Stage 5): Curriculum vs. Necessity Squeeze**
The Major Agent bridges the gap between biological learning styles (Stage 0) and the destination Job (Stage 4). It does NOT search "What is major X."
It hunts for structurally incompatible vehicles.

1. **Necessity Squeeze:** Student wants "Freelance UI Designer" but picks "Computer Science".
   Search: `"Do UI Designers actually need a CS degree vs alternative paths?"`
   Attack: The market doesn't require this. You are doing 4 years of math for a job that demands portfolios.
2. **Curriculum Squeeze:** Student is `hands-on` but picks a theoretical Vietnamese state university program.
   Search: `"Is [Major] in Vietnam theory-heavy or practical?"`
   Attack: Your brain needs to touch code. This program is 70% paper exams. You will suffer.

---

**[A22] University Agent (Stage 6): Vietnamese Higher-Ed Specialization & The Prestige/ROI Squeeze**
The University Agent is hard-coded as a Vietnamese Higher Education Specialist. The final roadblock forces the student to mathematically and culturally justify their choice of institution.

1. **The ROI Squeeze (Domestic):** Cross-checks tuition against their `goals.long.income_target`. If they demand RMIT but only want a $1k/mo relaxed job, the agent aggressively exposes the debt timeline.
2. **The Admissions Reality:** Searches exact 2024-2025 "điểm chuẩn" and aligns it with their effort (`summary`).
3. **The International Caveat:** If the student demands an international path (`campus_format="international"`), the Agent focuses purely on structural limits (Total Attendance Cost, Visa odds) and flips `is_domestic=False`, signaling the Output Compiler to render a warning block about international ignorance.

---

**[A23] Job & Major Agents (Stage 4 & 5): Vietnamese Ecosystem Protocol & The Dreamer Exception**
The Job and Major agents have been refactored to reject Western generic career advice and strictly enforce Vietnamese market realities.
1. **The Ecosystem Cap (Job):** Forces searches on the exact state of the VN market (e.g., "khó khăn khi làm [Role] ở Việt Nam", "mức lương thực tế"). Exposes the lack of niche roles or the outsourcing-heavy nature of local tech/creative hubs.
2. **The Trái Ngành & Lý Thuyết Limits (Major):** Forces queries against the brutal realities of the VN higher education system (high theory, outdated curriculums, massive out-of-field working rates).
3. **The Dreamer Exception:** The "Smart" path is taking a safe local degree. The "Dreamer" path is brute-forcing a niche passion. The agents are instructed NOT to crush the Dreamer's ambition IF the student has strong `purpose` and `goals` priors to survive the friction. It validates their ambition but forces them to face the exact, brutal execution barrier they must overcome without the help of the local ecosystem.

---

### 2026-04-02 — Session 4: Automated Evaluation Pipeline & Red-Teaming

**[A24] "Detail is not Defense" (Extractor Hallucination)**
Extractors were easily tricked by students providing hyper-detailed lifestyle fantasies (e.g., "I want to sit in a cafe in Da Lat and code remotely"). The LLM confused *vivid imagination* with *concrete sacrifice*, illegally boosting confidence to >0.7.
Decision: Inject `DETAIL IS NOT DEFENSE`. Detail without painful real-world cost is merely enthusiasm. Confidence MUST remain capped at <0.6.

**[A25] The Contradiction Drop (Semantic Deadlock)**
Extractors had a rule: `NEVER overwrite a field > 0.7 unless the student explicitly changed their mind`. This meant if a student locked in work as a "calling" (0.9), but later revealed their true goal is to "FIRE and retire completely at 35," the LLM refused to lower the "calling" confidence because the student didn't formally retract the word.
Decision: Implement `CONTRADICTION DROP`. If a logical contradiction surfaces against a locked prior, the LLM is ordered to violently override the confidence back down to `<0.5 (unclear)` to break the deadlock and force a Squeeze.

**[A26] TENSION EMBEDDING in the PROBE Anchor**
Analysts were successfully noting cross-field crashes (e.g. "prior says structured, but student wants digital nomad") in their free-form reasoning, but their final `PROBE:` anchor was too generic ("stress test their location choice"). The Output Compiler needs the tension handed to it.
Decision: Enforce `TENSION EMBEDDING`. The text of the `PROBE:` string MUST literally start by stating the exact prior-vs-claim conflict, forcing the compiler to aggressively weaponize the contradiction.

**[A27] Prior Agreement Is Not Defense**
Extractors were still vulnerable to a subtle failure mode: if a polished self-report happened to align with a seeded prior, the model would treat the agreement itself as verification and illegally push the field above the `0.6` cap. This surfaced in the Thinking re-audit when "abstract intellectual" language plus quiz alignment inflated `learning_mode` to `0.74` without any squeeze-and-sacrifice evidence.
Decision: Priors can suggest a candidate label, but they can NEVER verify a conversational field by themselves. Explicit rule added: `PRIOR AGREEMENT IS NOT DEFENSE`. Related rule: `DETAIL IS NOT DEFENSE` - vivid or high-status wording without a real trade-off still stays under the self-report cap.
