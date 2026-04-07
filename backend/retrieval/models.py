from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    vertical: Literal["general", "news", "reddit"] = "general"
    domains_allowlist: list[str] = Field(default_factory=list)
    max_results: int = 5
    fetch_mode: Literal["snippets_only", "extract_top_hits"] = "snippets_only"
    subreddit: str | None = None
    freshness_days: int | None = None


class SearchHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = ""
    url: str = ""
    snippet: str = ""
    domain: str = ""
    provider: str = ""
    published_at: str | None = None
    extracted_text: str = ""
    extraction_method: str | None = None


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    vertical: Literal["general", "news", "reddit"]
    provider_chain: list[str] = Field(default_factory=list)
    hits: list[SearchHit] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    quota_state: dict[str, Any] = Field(default_factory=dict)

