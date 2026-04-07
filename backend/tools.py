from langchain_core.tools import tool

from backend.retrieval import (
    SearchRequest,
    extract_url,
    format_search_response,
    search_reddit,
    search_web,
)

@tool
def search(query: str) -> str:
    """Search the web with the shared retrieval stack.
    Uses Serper first when quota is available, then falls back to DuckDuckGo.
    Use this when you need real facts about: job salaries, required skills,
    career paths, hiring trends, curriculum structure, or company types in Vietnam.
    Input should be a specific, targeted search query in Vietnamese.
    Prefer narrow contradiction-focused queries over one broad research request.
    Add `site:` filters when source quality matters.
    """
    response = search_web(
        SearchRequest(
            query=query,
            vertical="general",
            max_results=5,
            fetch_mode="snippets_only",
        )
    )
    return format_search_response(response, include_extracted=False)


@tool
def search_news(query: str) -> str:
    """Search current news using the shared free-first retrieval stack."""
    response = search_web(
        SearchRequest(
            query=query,
            vertical="news",
            max_results=5,
            fetch_mode="snippets_only",
        )
    )
    return format_search_response(response, include_extracted=False)


@tool
def reddit_search(query: str, subreddit: str = "") -> str:
    """Search Reddit using PRAW when configured, or DuckDuckGo site:reddit fallback."""
    response = search_reddit(
        SearchRequest(
            query=query,
            vertical="reddit",
            subreddit=subreddit or None,
            max_results=5,
            fetch_mode="snippets_only",
        )
    )
    return format_search_response(response, include_extracted=False)


@tool
def read_url(url: str, prefer_js: bool = False) -> str:
    """Extract readable content from a URL with Jina Reader first and Crawl4AI fallback."""
    text, method = extract_url(url, prefer_js=prefer_js)
    return f"Extraction method: {method}\nURL: {url}\nContent:\n{text}"
