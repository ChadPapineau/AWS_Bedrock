"""AgentCore Gateway Lambda -- MCP Tool Server.

Receives MCP tool invocation requests from AgentCore Gateway and routes
them to external APIs (Tavily web search, GitHub API).
"""

import json
import os
import urllib.request
import urllib.error


def _get_secret(secret_arn: str) -> str:
    """Retrieve a secret value from AWS Secrets Manager via boto3."""
    if not secret_arn:
        return ""
    import boto3
    client = boto3.client("secretsmanager")
    resp = client.get_secret_value(SecretId=secret_arn)
    return resp["SecretString"]


def _tavily_search(query: str, max_results: int = 5) -> dict:
    api_key = _get_secret(os.environ.get("TAVILY_API_KEY_SECRET_ARN", ""))
    if not api_key:
        return {"error": "Tavily API key not configured"}

    data = json.dumps({
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
    }).encode()

    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read())


def _github_search(query: str, search_type: str = "repositories", max_results: int = 5) -> dict:
    token = _get_secret(os.environ.get("GITHUB_TOKEN_SECRET_ARN", ""))
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/search/{search_type}?q={query}&per_page={max_results}&sort=stars&order=desc"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read())


TOOL_HANDLERS = {
    "web_search": _tavily_search,
    "github_search": _github_search,
}


def lambda_handler(event, context):
    """MCP tool server entrypoint."""
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}

    tool_name = body.get("tool")
    params = body.get("parameters", {})

    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(TOOL_HANDLERS.keys()),
            }),
        }

    try:
        result = handler(**params)
        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as exc:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(exc)}),
        }
