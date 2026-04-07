"""
Domain allowlists and search-source seeds for retrieval stages.

These are not hard enforcement rules yet. They are the curated domain sets that a future
research planner / query builder can use to add `site:` filters or prioritize source quality.
"""

JOB_MARKET_DOMAINS: tuple[str, ...] = (
    "itviec.com",
    "topcv.vn",
    "vietnamworks.com",
    "careerviet.vn",
    "glints.com",
    "jobstreet.vn",
)

JOB_SALARY_DOMAINS: tuple[str, ...] = (
    "itviec.com",
    "topcv.vn",
    "vietnamworks.com",
    "glints.com",
)

JOB_ROLE_REALITY_DOMAINS: tuple[str, ...] = (
    "itviec.com",
    "topcv.vn",
    "glints.com",
    "careerbuilder.vn",
)

MAJOR_REALITY_DOMAINS: tuple[str, ...] = (
    "moet.gov.vn",
    "topcv.vn",
    "glints.com",
    "thanhnien.vn",
    "tuoitre.vn",
)

UNIVERSITY_OFFICIAL_DOMAINS: tuple[str, ...] = (
    "moet.gov.vn",
    "vnu.edu.vn",
    "vnuhcm.edu.vn",
    "hust.edu.vn",
    "hcmut.edu.vn",
    "ftu.edu.vn",
    "neu.edu.vn",
)

UNIVERSITY_ADMISSIONS_DOMAINS: tuple[str, ...] = (
    "moet.gov.vn",
    "thanhnien.vn",
    "tuoitre.vn",
    "dantri.com.vn",
)

REDDIT_SEARCH_DOMAINS: tuple[str, ...] = (
    "reddit.com",
    "old.reddit.com",
)

REDDIT_FETCH_OPTIONS: dict[str, str] = {
    "official_data_api": (
        "Preferred when we need structured Reddit data. Requires a registered OAuth client, "
        "a descriptive User-Agent, and compliance with Reddit Data API terms."
    ),
    "search_engine_fallback": (
        "Use Serper with `site:reddit.com` or `site:old.reddit.com` when the API is not "
        "available and we only need discovery, not reliable thread extraction."
    ),
    "legacy_json_endpoints": (
        "Possible legacy fallback for read-only experiments, but treat as unstable. "
        "Reddit's own Data API wiki says some legacy documentation is out of date."
    ),
}
