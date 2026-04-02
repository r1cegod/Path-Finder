from typing import Final, Literal


StageName = Literal["thinking", "purpose", "goals", "job", "major", "university"]

STAGE_ORDER: Final[tuple[StageName, ...]] = (
    "thinking",
    "purpose",
    "goals",
    "job",
    "major",
    "university",
)

STAGE_INDEX: Final[dict[StageName, int]] = {name: i for i, name in enumerate(STAGE_ORDER)}

STAGE_TO_PROFILE_KEY: Final[dict[StageName, str]] = {
    "thinking": "thinking",
    "purpose": "purpose",
    "goals": "goals",
    "job": "job",
    "major": "major",
    "university": "university",
}

STAGE_TO_REASONING_KEY: Final[dict[StageName, str]] = {
    "thinking": "thinking",
    "purpose": "purpose",
    "goals": "goals",
    "job": "job",
    "major": "major",
    "university": "uni",
}

STAGE_TO_QUEUE_KEY: Final[dict[StageName, str]] = {
    "thinking": "thinking_style_message",
    "purpose": "purpose_message",
    "goals": "goals_message",
    "job": "job_message",
    "major": "major_message",
    "university": "uni_message",
}

VALID_STAGE_NAMES: Final[frozenset[str]] = frozenset(STAGE_ORDER)


def is_stage_name(value: str) -> bool:
    return value in VALID_STAGE_NAMES