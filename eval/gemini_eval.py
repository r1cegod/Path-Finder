"""
Gemini CLI evaluator wrapper for PathFinder.

Calls: gemini -p "<prompt>" -m gemini-2.5-pro -o json
Parses: response field → strips markdown code fences → returns dict

NOTE: The global GEMINI.md at C:/Users/r1ceg/.gemini/GEMINI.md (Antigravity persona)
is loaded on every call. We override it with OVERRIDE DIRECTIVE at the top of each prompt.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

GEMINI_MODEL = "gemini-2.5-flash"

# On Windows, `gemini` is an npm .cmd shim — subprocess needs the .cmd extension.
# On Unix/bash, the bare name works fine.
_GEMINI_CMD = "gemini.cmd" if sys.platform == "win32" else "gemini"

# ─── Override directive ────────────────────────────────────────────────────────
# Antigravity persona is injected from global GEMINI.md on every call.
# This block tells the model to drop that role for evaluation tasks.
_OVERRIDE = """\
OVERRIDE DIRECTIVE: You are PathFinder-Eval, a strict AI output evaluation judge.
Your ONLY task this call is to score AI counselor output. Disregard your Antigravity
coaching role entirely. Do not coach. Do not plan. Only judge.\n\n"""

# ─── Rubric template ──────────────────────────────────────────────────────────
_RUBRIC = """\
═══════════════════════════════════════════════
 EVALUATION TASK — PathFinder Stage: {stage}
 Persona: {persona}
═══════════════════════════════════════════════

CONVERSATION (assistant + user turns):
{conversation}

── EXPECTED PROFILE (ground truth) ──
{expected_profile}

── ACTUAL EXTRACTED PROFILE (agent output) ──
{actual_profile}

═══════════════════════════════════════════════
 SCORING RUBRIC (each dimension: 1–10 int)
═══════════════════════════════════════════════

1. field_extraction
   Did the agent correctly extract field values from the conversation?
   10 = all fields match expected map
   5  = some correct, some missing or wrong
   1  = most fields wrong or not extracted

2. confidence_calibration
   Are confidence scores (0.0–1.0) appropriate for evidence quality?
   10 = high conf for clear answers, low conf for vague/contradicted
   5  = mostly right but some miscalibrated
   1  = confidence doesn't reflect evidence at all

3. stage_completion
   Did the agent correctly detect when the stage was done (done=True)?
   10 = timing perfect, done flag correct
   5  = close but slightly early/late
   1  = set done=True prematurely OR never completed a complete stage

4. adversarial_handling
   Cooperative persona  → score how cleanly the agent moved through the happy path
   Red-team persona     → score how well it detected contradictions/trolling/drift
   10 = perfect detection + correct response (boundaries, redirects, escalation)
   5  = partial — caught some signals, missed others
   1  = missed signals entirely OR escalated incorrectly

5. vietnamese_quality
   Is the agent's Vietnamese natural and culturally appropriate?
   10 = sounds like a real Vietnamese counselor
   5  = correct but stiff or mechanical
   1  = unnatural register or inappropriate tone

Return ONLY valid JSON. No other text outside the JSON block:
{{
  "field_extraction": <int 1-10>,
  "confidence_calibration": <int 1-10>,
  "stage_completion": <int 1-10>,
  "adversarial_handling": <int 1-10>,
  "vietnamese_quality": <int 1-10>,
  "overall": <int 1-10>,
  "notes": "<1-2 sentences of key observations>"
}}
"""

# ─── Output rubric for output_graph cases ────────────────────────────────────
_OUTPUT_RUBRIC = """\
═══════════════════════════════════════════════
 EVALUATION TASK — PathFinder Output Compiler
 Case: {case}
═══════════════════════════════════════════════

STATE SNAPSHOT (what the output compiler received):
{state_snapshot}

COMPILER OUTPUT (what the agent actually said):
{actual_output}

EXPECTED BEHAVIOR:
{expected_behavior}

═══════════════════════════════════════════════
 SCORING RUBRIC (each dimension: 1–10 int)
═══════════════════════════════════════════════

1. case_routing
   Did the compiler correctly identify which case (A/B1/B2/C) applies?
   10 = correct case, correct output mode
   1  = wrong case routing

2. content_accuracy
   Is the output content appropriate for the case?
   Case A  → acknowledge non-stage input, pivot back
   Case B1 → continue drilling the incomplete stage
   Case B2 → trigger path debate framing
   Case C  → terminate gracefully with handoff message
   10 = content perfectly matches expected behavior
   1  = wrong content entirely

3. vietnamese_quality
   Natural Vietnamese, correct register for each case.
   10 = sounds like real counselor
   1  = mechanical or wrong register

4. boundary_enforcement
   For Case C: did the model terminate correctly without being preachy?
   For other cases: does the response stay within scope?
   10 = clean execution
   1  = overstepped or underdelivered

Return ONLY valid JSON:
{{
  "case_routing": <int 1-10>,
  "content_accuracy": <int 1-10>,
  "vietnamese_quality": <int 1-10>,
  "boundary_enforcement": <int 1-10>,
  "overall": <int 1-10>,
  "notes": "<1-2 sentences>"
}}
"""


_SETTINGS_PATH = Path.home() / ".gemini" / "settings.json"


def _patch_settings_model(model: str) -> str:
    """
    Swap settings.json model.name to `model`. Returns the original name.
    settings.json always wins over -m flag in this CLI version.
    """
    data = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    original = data.get("model", {}).get("name", GEMINI_MODEL)
    data.setdefault("model", {})["name"] = model
    _SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return original


def _strip_fences(text: str) -> str:
    """Strip ```json ... ``` markdown fences from Gemini response."""
    return re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()


def call_gemini(prompt: str, model: str = GEMINI_MODEL) -> str:
    """
    Call gemini CLI in headless mode.
    Returns the raw response text (before JSON parsing).

    Patches settings.json before the call and restores it after —
    because the CLI ignores -m when settings.json has a model override.
    Raises RuntimeError if CLI exits non-zero.
    """
    original_model = _patch_settings_model(model)
    try:
        result = subprocess.run(
            [_GEMINI_CMD, "-p", prompt, "-m", model, "-o", "json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    finally:
        _patch_settings_model(original_model)  # always restore

    if result.returncode != 0:
        raise RuntimeError(
            f"gemini CLI error (code {result.returncode}):\n{result.stderr[:500]}"
        )
    try:
        raw = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse gemini CLI stdout as JSON: {e}\nRaw: {result.stdout[:300]}")
    return raw["response"]


def evaluate_stage(
    stage: str,
    persona: str,
    conversation: list[tuple[str, str]],
    expected_profile: dict,
    actual_profile: dict,
    model: str = GEMINI_MODEL,
) -> dict:
    """
    Evaluate one stage thread result.

    Args:
        stage:            Stage name ("thinking", "purpose", "goals", "job", "major", "uni")
        persona:          "cooperative" or "red_team"
        conversation:     List of (role, content) — role is "assistant" or "user"
        expected_profile: Ground truth map from thread metadata
        actual_profile:   Extracted profile dict from graph output

    Returns:
        Dict with keys: field_extraction, confidence_calibration, stage_completion,
        adversarial_handling, vietnamese_quality, overall, notes
    """
    conv_str = "\n".join(
        f"[{role.upper()}]: {content}" for role, content in conversation
    )
    prompt = _OVERRIDE + _RUBRIC.format(
        stage=stage,
        persona=persona,
        conversation=conv_str,
        expected_profile=json.dumps(expected_profile, ensure_ascii=False, indent=2),
        actual_profile=json.dumps(actual_profile, ensure_ascii=False, indent=2),
    )
    response_text = call_gemini(prompt, model=model)
    return json.loads(_strip_fences(response_text))


def evaluate_output(
    case: str,
    state_snapshot: dict,
    actual_output: str,
    expected_behavior: str,
    model: str = GEMINI_MODEL,
) -> dict:
    """
    Evaluate one output compiler case result.

    Args:
        case:             "A", "B1", "B2", or "C"
        state_snapshot:   Relevant fields from PathFinderState before compiler ran
        actual_output:    The compiler's AIMessage content
        expected_behavior: Free-text description of what should happen

    Returns:
        Dict with keys: case_routing, content_accuracy, vietnamese_quality,
        boundary_enforcement, overall, notes
    """
    prompt = _OVERRIDE + _OUTPUT_RUBRIC.format(
        case=case,
        state_snapshot=json.dumps(state_snapshot, ensure_ascii=False, indent=2),
        actual_output=actual_output,
        expected_behavior=expected_behavior,
    )
    response_text = call_gemini(prompt, model=model)
    return json.loads(_strip_fences(response_text))
