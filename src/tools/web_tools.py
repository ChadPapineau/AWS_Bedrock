"""Web research tools for the Scout agent.

Provides web search, GitHub repository search, and URL content fetching
via external APIs (Tavily for web search, GitHub REST API).
"""

from __future__ import annotations

import json
import logging

import httpx
from strands import tool

from src.config import settings

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT = 30.0


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for current information on a topic.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5).

    Returns:
        A formatted string of search results with titles, URLs, and snippets.
    """
    api_key = settings.tavily_api_key
    if not api_key:
        return (
            "ERROR: TAVILY_API_KEY is not configured. "
            "Set it in your .env file to enable web search."
        )

    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": True,
                    "search_depth": "advanced",
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.error("Tavily search failed: %s", exc)
        return f"ERROR: Web search request failed: {exc}"

    results = data.get("results", [])
    if not results:
        return f"No web results found for: {query}"

    lines: list[str] = []
    answer = data.get("answer")
    if answer:
        lines.append(f"Quick Answer: {answer}\n")

    for i, r in enumerate(results, 1):
        lines.append(
            f"{i}. **{r.get('title', 'Untitled')}**\n"
            f"   URL: {r.get('url', 'N/A')}\n"
            f"   {r.get('content', '')[:300]}\n"
        )

    return "\n".join(lines)


@tool
def github_search(
    query: str,
    search_type: str = "repositories",
    max_results: int = 5,
) -> str:
    """Search GitHub for repositories, code, or issues.

    Args:
        query: The search query (supports GitHub search qualifiers like 'language:python stars:>100').
        search_type: One of 'repositories', 'code', or 'issues'. Default 'repositories'.
        max_results: Maximum number of results to return (default 5).

    Returns:
        Formatted search results with key metadata.
    """
    token = settings.github_token
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    valid_types = {"repositories", "code", "issues"}
    if search_type not in valid_types:
        return f"ERROR: search_type must be one of {valid_types}"

    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            resp = client.get(
                f"https://api.github.com/search/{search_type}",
                params={"q": query, "per_page": max_results, "sort": "stars", "order": "desc"},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.error("GitHub search failed: %s", exc)
        return f"ERROR: GitHub search request failed: {exc}"

    items = data.get("items", [])
    if not items:
        return f"No GitHub {search_type} found for: {query}"

    lines: list[str] = [f"Found {data.get('total_count', '?')} {search_type} (showing top {len(items)}):\n"]

    if search_type == "repositories":
        for i, repo in enumerate(items, 1):
            lines.append(
                f"{i}. **{repo['full_name']}** ({repo.get('stargazers_count', 0)} stars)\n"
                f"   URL: {repo['html_url']}\n"
                f"   {repo.get('description', 'No description')}\n"
                f"   Language: {repo.get('language', 'N/A')} | "
                f"   Updated: {repo.get('updated_at', 'N/A')[:10]}\n"
            )
    elif search_type == "code":
        for i, item in enumerate(items, 1):
            lines.append(
                f"{i}. **{item['repository']['full_name']}** - {item['name']}\n"
                f"   Path: {item['path']}\n"
                f"   URL: {item['html_url']}\n"
            )
    elif search_type == "issues":
        for i, issue in enumerate(items, 1):
            lines.append(
                f"{i}. **{issue['title']}** (#{issue['number']})\n"
                f"   Repo: {issue['repository_url'].split('/repos/')[-1]}\n"
                f"   State: {issue['state']} | Labels: {', '.join(l['name'] for l in issue.get('labels', []))}\n"
                f"   URL: {issue['html_url']}\n"
            )

    return "\n".join(lines)


@tool
def fetch_url(url: str, max_length: int = 5000) -> str:
    """Fetch and extract text content from a URL.

    Args:
        url: The URL to fetch.
        max_length: Maximum characters of content to return (default 5000).

    Returns:
        The text content of the page, truncated to max_length.
    """
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "AgentCore-Scout/1.0"})
            resp.raise_for_status()
            content = resp.text
    except httpx.HTTPError as exc:
        logger.error("URL fetch failed for %s: %s", url, exc)
        return f"ERROR: Failed to fetch URL {url}: {exc}"

    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            return json.dumps(json.loads(content), indent=2)[:max_length]
        except json.JSONDecodeError:
            pass

    if len(content) > max_length:
        content = content[:max_length] + "\n\n... [truncated]"

    return content
