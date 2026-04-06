"""Tests for the Scout agent and its web tools."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.tools.web_tools import web_search, github_search, fetch_url


class TestWebSearch:
    def test_returns_error_when_api_key_missing(self):
        with patch("src.tools.web_tools.settings") as mock_settings:
            mock_settings.tavily_api_key = None
            result = web_search.fn(query="test query")
            assert "TAVILY_API_KEY is not configured" in result

    @patch("src.tools.web_tools.httpx.Client")
    def test_returns_formatted_results(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "Quick answer here",
            "results": [
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "content": "This is test content about secrets management.",
                },
            ],
        }
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with patch("src.tools.web_tools.settings") as mock_settings:
            mock_settings.tavily_api_key = "test-key"
            result = web_search.fn(query="secrets management tools")

        assert "Test Result" in result
        assert "https://example.com" in result
        assert "Quick answer here" in result

    @patch("src.tools.web_tools.httpx.Client")
    def test_handles_empty_results(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with patch("src.tools.web_tools.settings") as mock_settings:
            mock_settings.tavily_api_key = "test-key"
            result = web_search.fn(query="nonexistent topic xyz")

        assert "No web results found" in result


class TestGitHubSearch:
    @patch("src.tools.web_tools.httpx.Client")
    def test_returns_formatted_repo_results(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total_count": 1,
            "items": [
                {
                    "full_name": "hashicorp/vault",
                    "html_url": "https://github.com/hashicorp/vault",
                    "description": "A tool for secrets management",
                    "stargazers_count": 30000,
                    "language": "Go",
                    "updated_at": "2026-04-01T00:00:00Z",
                },
            ],
        }
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with patch("src.tools.web_tools.settings") as mock_settings:
            mock_settings.github_token = "test-token"
            result = github_search.fn(query="secrets management")

        assert "hashicorp/vault" in result
        assert "30000" in result

    def test_rejects_invalid_search_type(self):
        with patch("src.tools.web_tools.settings"):
            result = github_search.fn(query="test", search_type="invalid")
        assert "ERROR" in result


class TestFetchUrl:
    @patch("src.tools.web_tools.httpx.Client")
    def test_fetches_and_returns_content(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.text = "<html><body>Hello World</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = fetch_url.fn(url="https://example.com")
        assert "Hello World" in result

    @patch("src.tools.web_tools.httpx.Client")
    def test_truncates_long_content(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.text = "x" * 10000
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = fetch_url.fn(url="https://example.com", max_length=100)
        assert len(result) < 200
        assert "truncated" in result
