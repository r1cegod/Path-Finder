from __future__ import annotations

import re

from pydantic import BaseModel

from backend.data.contracts.confidence import (
    DONE_CONFIDENCE_THRESHOLD,
    REOPEN_CONFIDENCE_CEILING,
)
from backend.data.contracts.stages import STAGE_TO_REASONING_KEY, StageName
from backend.data.state import PathFinderState


FIELD_PATHS_BY_STAGE: dict[StageName, dict[str, tuple[str, ...]]] = {
    "thinking": {
        "learning_mode": ("learning_mode",),
        "env_constraint": ("env_constraint",),
        "social_battery": ("social_battery",),
        "personality_type": ("personality_type",),
    },
    "purpose": {
        "core_desire": ("core_desire",),
        "work_relationship": ("work_relationship",),
        "ai_stance": ("ai_stance",),
        "location_vision": ("location_vision",),
        "risk_philosophy": ("risk_philosophy",),
        "key_quote": ("key_quote",),
    },
    "goals": {
        "income_target": ("long", "income_target"),
        "autonomy_level": ("long", "autonomy_level"),
        "ownership_model": ("long", "ownership_model"),
        "team_size": ("long", "team_size"),
        "skill_targets": ("short", "skill_targets"),
        "portfolio_goal": ("short", "portfolio_goal"),
        "credential_needed": ("short", "credential_needed"),
    },
    "job": {
        "role_category": ("role_category",),
        "company_stage": ("company_stage",),
        "day_to_day": ("day_to_day",),
        "autonomy_level": ("autonomy_level",),
    },
    "major": {
        "field": ("field",),
        "curriculum_style": ("curriculum_style",),
        "required_skills_coverage": ("required_skills_coverage",),
    },
    "university": {
        "prestige_requirement": ("prestige_requirement",),
        "target_school": ("target_school",),
        "campus_format": ("campus_format",),
    },
}

DONE_FIELD_PATHS_BY_STAGE: dict[StageName, tuple[tuple[str, ...], ...]] = {
    "thinking": (
        ("learning_mode",),
        ("env_constraint",),
        ("social_battery",),
        ("personality_type",),
    ),
    "purpose": (
        ("core_desire",),
        ("work_relationship",),
        ("location_vision",),
        ("risk_philosophy",),
    ),
    "goals": (
        ("long", "income_target"),
        ("long", "ownership_model"),
        ("short", "skill_targets"),
        ("short", "portfolio_goal"),
    ),
    "job": (
        ("role_category",),
        ("company_stage",),
        ("day_to_day",),
        ("autonomy_level",),
    ),
    "major": (
        ("field",),
        ("curriculum_style",),
        ("required_skills_coverage",),
    ),
    "university": (
        ("prestige_requirement",),
        ("target_school",),
        ("campus_format",),
    ),
}


def _stage_context(state: PathFinderState, stage_name: StageName) -> tuple[str, str, str]:
    stage_raw = state.get("stage") or {}
    if isinstance(stage_raw, dict):
        current = str(stage_raw.get("current_stage") or stage_name)
        anchor = str(stage_raw.get("anchor_stage") or current)
        mode = str(stage_raw.get("anchor_mode") or "normal")
    else:
        current = str(getattr(stage_raw, "current_stage", stage_name) or stage_name)
        anchor = str(getattr(stage_raw, "anchor_stage", "") or current)
        mode = str(getattr(stage_raw, "anchor_mode", "normal") or "normal")
    return current, anchor, mode


def get_reentry_mode(state: PathFinderState, stage_name: StageName) -> str:
    current, anchor, mode = _stage_context(state, stage_name)
    if anchor == stage_name and anchor != current and mode in {"revisit", "forced"}:
        return mode
    return "normal"


def _is_reentry_transition(state: PathFinderState, stage_name: StageName) -> bool:
    current, anchor, mode = _stage_context(state, stage_name)
    if not state.get("stage_transitioned"):
        return False
    return anchor == stage_name and anchor != current and mode in {"revisit", "forced"}


def _read_stage_reasoning_text(state: PathFinderState, stage_name: StageName) -> str:
    key = STAGE_TO_REASONING_KEY[stage_name]
    raw = state.get("stage_reasoning") or {}
    if isinstance(raw, dict):
        return str(raw.get(key, "") or "")
    return str(getattr(raw, key, "") or "")


def _target_paths_for_reentry(state: PathFinderState, stage_name: StageName) -> tuple[tuple[str, ...], ...]:
    reasoning = _read_stage_reasoning_text(state, stage_name)
    match = re.search(r"(?im)^PROBE:\s*([a-zA-Z_]+)\b", reasoning)
    if match:
        path = FIELD_PATHS_BY_STAGE[stage_name].get(match.group(1))
        if path is not None:
            return (path,)
    return DONE_FIELD_PATHS_BY_STAGE[stage_name]


def _get_path(model: BaseModel, path: tuple[str, ...]) -> object:
    current: object = model
    for part in path:
        current = getattr(current, part)
    return current


def _set_path(model: BaseModel, path: tuple[str, ...], value: object) -> BaseModel:
    head = path[0]
    if len(path) == 1:
        return model.model_copy(update={head: value})
    child = getattr(model, head)
    updated_child = _set_path(child, path[1:], value)
    return model.model_copy(update={head: updated_child})


def _clamp_field(field: object) -> object:
    current = float(getattr(field, "confidence", 0.0) or 0.0)
    if current <= REOPEN_CONFIDENCE_CEILING:
        return field
    return field.model_copy(update={"confidence": REOPEN_CONFIDENCE_CEILING})


def apply_reopen_invalidation(
    state: PathFinderState,
    stage_name: StageName,
    profile: BaseModel,
) -> BaseModel:
    if not _is_reentry_transition(state, stage_name):
        return profile

    updated = profile
    for path in _target_paths_for_reentry(state, stage_name):
        field = _get_path(updated, path)
        clamped = _clamp_field(field)
        if clamped is not field:
            updated = _set_path(updated, path, clamped)
    return updated


def _field_is_done(field: object) -> bool:
    return float(getattr(field, "confidence", 0.0) or 0.0) > DONE_CONFIDENCE_THRESHOLD


def count_done_fields(stage_name: StageName, profile: BaseModel) -> tuple[int, int]:
    done_count = sum(
        1
        for path in DONE_FIELD_PATHS_BY_STAGE[stage_name]
        if _field_is_done(_get_path(profile, path))
    )
    return done_count, len(DONE_FIELD_PATHS_BY_STAGE[stage_name])


def normalize_stage_profile(stage_name: StageName, profile: BaseModel) -> BaseModel:
    done_count, done_total = count_done_fields(stage_name, profile)
    done = done_count == done_total
    updates: dict[str, object] = {}

    if getattr(profile, "done", done) != done:
        updates["done"] = done

    if stage_name == "goals":
        long_profile = getattr(profile, "long", None)
        short_profile = getattr(profile, "short", None)

        if long_profile is not None:
            long_done = all(
                _field_is_done(getattr(long_profile, field_name))
                for field_name in ("income_target", "autonomy_level", "ownership_model", "team_size")
            )
            if getattr(long_profile, "done", long_done) != long_done:
                updates["long"] = long_profile.model_copy(update={"done": long_done})

        if short_profile is not None:
            short_done = all(
                _field_is_done(getattr(short_profile, field_name))
                for field_name in ("skill_targets", "portfolio_goal", "credential_needed")
            )
            current_short = updates.get("short", short_profile)
            if getattr(current_short, "done", short_done) != short_done:
                updates["short"] = current_short.model_copy(update={"done": short_done})

    return profile.model_copy(update=updates) if updates else profile
