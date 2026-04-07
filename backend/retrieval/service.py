import asyncio
import os
import random
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper

from backend.retrieval.models import SearchHit, SearchRequest, SearchResponse
from backend.retrieval.quota import can_use_serper, load_usage_state, mark_serper_call

load_dotenv()

DDG_JITTER_SECONDS = (3.0, 5.0)
DEFAULT_TIMEOUT = 20.0
DEFAULT_USER_AGENT = "PathFinder Retrieval Layer/1.0"

try:
    from ddgs import DDGS
except ImportError:  # pragma: no cover - optional runtime dependency
    try:
        from duckduckgo_search import DDGS
    except ImportError:  # pragma: no cover - optional runtime dependency
        DDGS = None

try:
    import praw
except ImportError:  # pragma: no cover - optional runtime dependency
    praw = None

try:
    import feedparser
except ImportError:  # pragma: no cover - optional runtime dependency
    feedparser = None


def _normalize_domain(url: str) -> str:
    if not url:
        return ""
    return (urlparse(url).netloc or "").lower().removeprefix("www.")


def _apply_ddg_jitter() -> None:
    time.sleep(random.uniform(*DDG_JITTER_SECONDS))


def _build_query(query: str, domains_allowlist: list[str]) -> str:
    if not domains_allowlist:
        return query

    domain_clause = " OR ".join(f"site:{domain}" for domain in domains_allowlist)
    return f"{query} ({domain_clause})"


def _clip(text: str, limit: int = 700) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def _client_headers() -> dict[str, str]:
    return {"User-Agent": os.getenv("REDDIT_USER_AGENT") or DEFAULT_USER_AGENT}


def _search_serper(request: SearchRequest) -> SearchResponse:
    wrapper = GoogleSerperAPIWrapper(k=request.max_results, gl="vn", hl="vi")
    query = _build_query(request.query, request.domains_allowlist)
    raw = wrapper.results(query)
    quota_state = mark_serper_call()

    hits: list[SearchHit] = []
    for item in raw.get("organic", [])[: request.max_results]:
        hits.append(
            SearchHit(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                domain=_normalize_domain(item.get("link", "")),
                provider="serper",
                published_at=item.get("date"),
            )
        )

    return SearchResponse(
        query=request.query,
        vertical=request.vertical,
        provider_chain=["serper"],
        hits=hits,
        quota_state=quota_state,
    )


def _search_ddg_text(request: SearchRequest) -> SearchResponse:
    if DDGS is None:
        raise RuntimeError("duckduckgo-search is not installed")

    _apply_ddg_jitter()
    query = _build_query(request.query, request.domains_allowlist)
    with DDGS() as ddgs:
        raw_hits = list(ddgs.text(query, max_results=request.max_results))
        if not raw_hits and request.domains_allowlist:
            raw_hits = list(ddgs.text(request.query, max_results=request.max_results))

    hits = [
        SearchHit(
            title=item.get("title", ""),
            url=item.get("href", ""),
            snippet=item.get("body", ""),
            domain=_normalize_domain(item.get("href", "")),
            provider="ddg",
        )
        for item in raw_hits[: request.max_results]
    ]

    return SearchResponse(
        query=request.query,
        vertical=request.vertical,
        provider_chain=["ddg_text"],
        hits=hits,
        quota_state=load_usage_state(),
    )


def _search_ddg_news(request: SearchRequest) -> SearchResponse:
    if DDGS is None:
        raise RuntimeError("duckduckgo-search is not installed")

    _apply_ddg_jitter()
    query = _build_query(request.query, request.domains_allowlist)
    with DDGS() as ddgs:
        raw_hits = list(ddgs.news(query, max_results=request.max_results))
        if not raw_hits and request.domains_allowlist:
            raw_hits = list(ddgs.news(request.query, max_results=request.max_results))

    hits = [
        SearchHit(
            title=item.get("title", ""),
            url=item.get("url", ""),
            snippet=item.get("body", ""),
            domain=_normalize_domain(item.get("url", "")),
            provider="ddg_news",
            published_at=item.get("date"),
        )
        for item in raw_hits[: request.max_results]
    ]

    return SearchResponse(
        query=request.query,
        vertical=request.vertical,
        provider_chain=["ddg_news"],
        hits=hits,
        quota_state=load_usage_state(),
    )


def _reddit_client():
    if praw is None:
        return None

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")
    if not (client_id and client_secret and user_agent):
        return None

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def _search_reddit_praw(request: SearchRequest) -> SearchResponse:
    client = _reddit_client()
    if client is None:
        raise RuntimeError("Reddit API credentials are not configured")

    target = client.subreddit(request.subreddit or "all")
    hits: list[SearchHit] = []
    for submission in target.search(request.query, limit=request.max_results, sort="relevance"):
        published = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).isoformat()
        hits.append(
            SearchHit(
                title=submission.title or "",
                url=f"https://www.reddit.com{submission.permalink}",
                snippet=_clip(submission.selftext or ""),
                domain="reddit.com",
                provider="praw",
                published_at=published,
            )
        )

    return SearchResponse(
        query=request.query,
        vertical=request.vertical,
        provider_chain=["praw"],
        hits=hits,
        quota_state=load_usage_state(),
    )


def fetch_reddit_rss(feed_url: str) -> list[dict[str, str]]:
    if feedparser is None:
        raise RuntimeError("feedparser is not installed")

    feed = feedparser.parse(feed_url)
    entries: list[dict[str, str]] = []
    for entry in getattr(feed, "entries", []):
        entries.append(
            {
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": _clip(entry.get("summary", ""), 400),
            }
        )
    return entries


def fetch_reddit_json(url: str) -> dict:
    json_url = url if url.endswith(".json") else f"{url.rstrip('/')}.json"
    response = httpx.get(json_url, headers=_client_headers(), timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _search_reddit_fallback(request: SearchRequest) -> SearchResponse:
    fallback_query = request.query
    if request.subreddit:
        fallback_query = f"{fallback_query} site:reddit.com/r/{request.subreddit}"
    else:
        fallback_query = f"{fallback_query} site:reddit.com"

    fallback_request = request.model_copy(
        update={
            "query": fallback_query,
            "vertical": "general",
            "domains_allowlist": ["reddit.com", "old.reddit.com"],
        }
    )
    response = _search_ddg_text(fallback_request)
    return response.model_copy(
        update={
            "query": request.query,
            "vertical": "reddit",
            "provider_chain": ["ddg_text_reddit_fallback"],
        }
    )


def _extract_with_jina(url: str) -> tuple[str, str]:
    if url.startswith("http://"):
        target = f"https://r.jina.ai/http://{url[len('http://'):]}"
    elif url.startswith("https://"):
        target = f"https://r.jina.ai/http://{url[len('https://'):]}"
    else:
        target = f"https://r.jina.ai/http://{url}"

    response = httpx.get(target, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.text, "jina_reader"


def _extract_with_crawl4ai(url: str) -> tuple[str, str]:
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError as exc:  # pragma: no cover - optional runtime dependency
        raise RuntimeError("crawl4ai is not installed") from exc

    async def _run() -> tuple[str, str]:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            markdown = getattr(result, "markdown", "") or getattr(result, "cleaned_html", "")
            return markdown, "crawl4ai"

    return asyncio.run(_run())


def extract_url(url: str, prefer_js: bool = False) -> tuple[str, str]:
    methods = [_extract_with_crawl4ai, _extract_with_jina] if prefer_js else [_extract_with_jina, _extract_with_crawl4ai]
    last_error = None
    for method in methods:
        try:
            return method(url)
        except Exception as exc:  # pragma: no cover - network/provider failures
            last_error = exc
    raise RuntimeError(f"Could not extract content from {url}") from last_error


def _maybe_extract_top_hits(response: SearchResponse, request: SearchRequest) -> SearchResponse:
    if request.fetch_mode != "extract_top_hits":
        return response

    updated_hits: list[SearchHit] = []
    for index, hit in enumerate(response.hits):
        if index >= 2 or not hit.url:
            updated_hits.append(hit)
            continue
        try:
            text, method = extract_url(hit.url)
            updated_hits.append(
                hit.model_copy(update={"extracted_text": _clip(text, 1500), "extraction_method": method})
            )
        except Exception as exc:  # pragma: no cover - network/provider failures
            updated_hits.append(hit)
            response.warnings.append(f"Extraction failed for {hit.url}: {exc}")
    return response.model_copy(update={"hits": updated_hits})


def search_web(request: SearchRequest) -> SearchResponse:
    warnings: list[str] = []

    if request.vertical == "news":
        response = _search_ddg_news(request)
        return _maybe_extract_top_hits(response, request)

    if os.getenv("SERPER_API_KEY") and can_use_serper():
        try:
            response = _search_serper(request)
            return _maybe_extract_top_hits(response, request)
        except Exception as exc:  # pragma: no cover - provider failures
            warnings.append(f"Serper failed: {exc}")

    response = _search_ddg_text(request)
    if warnings:
        response.warnings.extend(warnings)
    return _maybe_extract_top_hits(response, request)


def search_reddit(request: SearchRequest) -> SearchResponse:
    if request.vertical != "reddit":
        request = request.model_copy(update={"vertical": "reddit"})

    try:
        return _search_reddit_praw(request)
    except Exception as exc:  # pragma: no cover - missing credentials/provider failures
        response = _search_reddit_fallback(request)
        response.warnings.append(f"PRAW unavailable, used fallback: {exc}")
        return response


def format_search_response(response: SearchResponse, include_extracted: bool = True) -> str:
    lines = [
        f"Query: {response.query}",
        f"Vertical: {response.vertical}",
        f"Provider chain: {', '.join(response.provider_chain) if response.provider_chain else 'none'}",
    ]
    if response.warnings:
        lines.append("Warnings:")
        for warning in response.warnings:
            lines.append(f"- {warning}")

    if response.quota_state:
        calls = response.quota_state.get("serper_calls")
        limit = response.quota_state.get("serper_limit")
        lines.append(f"Quota: serper_calls={calls}/{limit}")

    lines.append("Results:")
    if not response.hits:
        lines.append("- No results found")
        return "\n".join(lines)

    for hit in response.hits:
        lines.append(f"- {hit.title}")
        lines.append(f"  URL: {hit.url}")
        if hit.snippet:
            lines.append(f"  Snippet: {_clip(hit.snippet, 350)}")
        if include_extracted and hit.extracted_text:
            lines.append(f"  Extracted: {_clip(hit.extracted_text, 700)}")

    return "\n".join(lines)
