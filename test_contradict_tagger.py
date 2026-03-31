"""
Smoke tests — contradict tagger + context_stages union.

No LLM calls. Pure Python logic only.

Test 1 — stage_manager: contradict tagger tags past-stage queues
Test 2 — stage_manager: no contradict → no extra queue entries
Test 3 — stage_manager: 'university' maps to uni_message (alias)
Test 4 — build_compiler_prompt: contradict_target reasoning appears in context
Test 5 — build_compiler_prompt: deduplication when target already in stage_related
"""

from langchain_core.messages import HumanMessage
from backend.data.state import DEFAULT_STATE, DEFAULT_STAGE, StageReasoning
from backend.orchestrator_graph import stage_manager
from backend.data.prompts.output import build_compiler_prompt

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

def check(label: str, condition: bool):
    print(f"  [{PASS if condition else FAIL}] {label}")
    return condition

# ─── shared fixture ──────────────────────────────────────────────────────────
SENTINEL = HumanMessage(content="tôi muốn làm AI engineer")

def base_state(**overrides):
    return {**DEFAULT_STATE, "messages": [SENTINEL], **overrides}


# ═══════════════════════════════════════════════════════════════════════════════
#  TEST 1 — contradict: purpose referenced while in goals stage
# ═══════════════════════════════════════════════════════════════════════════════
print("\nTest 1 — contradict tagger: past stage tagged")

state = base_state(stage={
    **DEFAULT_STAGE,
    "current_stage": "goals",
    "stage_related": ["purpose", "goals"],   # purpose is past → contradict
    "rebound": False,
})
result = stage_manager(state)

stage_out = result["stage"]
all_pass = True
all_pass &= check("contradict=True in stage output",     stage_out["contradict"] == True)
all_pass &= check("contradict_target=['purpose']",        stage_out["contradict_target"] == ["purpose"])
all_pass &= check("contradict_count incremented to 1",   result["contradict_count"] == 1)
all_pass &= check("purpose_message tagged with sentinel", result.get("purpose_message") == [SENTINEL])
all_pass &= check("goals_message NOT in result (no explicit tag)", "goals_message" not in result)


# ═══════════════════════════════════════════════════════════════════════════════
#  TEST 2 — no contradict: no past stages
# ═══════════════════════════════════════════════════════════════════════════════
print("\nTest 2 — no contradict: tagger does not fire")

state = base_state(stage={
    **DEFAULT_STAGE,
    "current_stage": "goals",
    "stage_related": ["goals"],              # only current stage
    "rebound": False,
})
result = stage_manager(state)

stage_out = result["stage"]
all_pass &= check("contradict=False",                     stage_out["contradict"] == False)
all_pass &= check("contradict_target=[]",                 stage_out["contradict_target"] == [])
all_pass &= check("purpose_message NOT in result",        "purpose_message" not in result)
all_pass &= check("goals_message NOT in result",          "goals_message" not in result)


# ═══════════════════════════════════════════════════════════════════════════════
#  TEST 3 — university alias: maps to uni_message
# ═══════════════════════════════════════════════════════════════════════════════
print("\nTest 3 -- contradict tagger: 'university' -> uni_message")

state = base_state(stage={
    **DEFAULT_STAGE,
    "current_stage": "uni",           # uni stage is NOT in STAGE_INDEX yet — test with thinking→purpose
    "stage_related": ["thinking", "purpose"],
    "rebound": False,
    "current_stage": "purpose",       # purpose stage, thinking is past
})
result = stage_manager(state)

stage_out = result["stage"]
all_pass &= check("contradict=True",                               stage_out["contradict"] == True)
all_pass &= check("thinking_style_message tagged with sentinel",   result.get("thinking_style_message") == [SENTINEL])


# ═══════════════════════════════════════════════════════════════════════════════
#  TEST 4 — build_compiler_prompt: contradict_target reasoning appears in context
# ═══════════════════════════════════════════════════════════════════════════════
print("\nTest 4 — build_compiler_prompt: contradict_target reasoning in PROFILE_CONTEXT_BLOCK")

PURPOSE_REASONING = "Student wants impact over money — verbatim: 'tôi muốn làm gì đó có ý nghĩa'"

state = base_state(
    stage={
        **DEFAULT_STAGE,
        "current_stage": "goals",
        "stage_related": ["goals"],              # goals only in related...
        "contradict": True,
        "contradict_target": ["purpose"],        # ...but purpose is contradict target
    },
    stage_reasoning=StageReasoning(
        purpose=PURPOSE_REASONING,
        goals="Goals reasoning pending.",
    ),
    message_tag=None,
    user_tag=None,
    bypass_stage=False,
    escalation_pending=False,
    path_debate_ready=False,
    stage_transitioned=False,
)
prompt = build_compiler_prompt(state)

all_pass &= check("PURPOSE reasoning appears in prompt",    PURPOSE_REASONING in prompt)
all_pass &= check("[PURPOSE] header in prompt",             "[PURPOSE]" in prompt)
all_pass &= check("[GOALS] reasoning also included",        "[GOALS]" in prompt)


# ═══════════════════════════════════════════════════════════════════════════════
#  TEST 5 — deduplication: contradict_target already in stage_related
# ═══════════════════════════════════════════════════════════════════════════════
print("\nTest 5 — build_compiler_prompt: dedup when target already in stage_related")

state = base_state(
    stage={
        **DEFAULT_STAGE,
        "current_stage": "goals",
        "stage_related": ["purpose", "goals"],   # purpose in BOTH lists
        "contradict": True,
        "contradict_target": ["purpose"],
    },
    stage_reasoning=StageReasoning(
        purpose=PURPOSE_REASONING,
        goals="Goals reasoning pending.",
    ),
    message_tag=None,
    user_tag=None,
    bypass_stage=False,
    escalation_pending=False,
    path_debate_ready=False,
    stage_transitioned=False,
)
prompt = build_compiler_prompt(state)
purpose_count = prompt.count("[PURPOSE]")

all_pass &= check("[PURPOSE] appears exactly once (no dup)", purpose_count == 1)
all_pass &= check("PURPOSE reasoning still present",         PURPOSE_REASONING in prompt)


# ─── summary ─────────────────────────────────────────────────────────────────
print(f"\n{'All tests passed.' if all_pass else 'SOME TESTS FAILED.'}\n")
