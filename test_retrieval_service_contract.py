import unittest
from unittest.mock import patch

from backend.retrieval import SearchHit, SearchRequest, SearchResponse, format_search_response
from backend.retrieval.service import search_reddit, search_web


def _response(provider: str, vertical: str = "general") -> SearchResponse:
    return SearchResponse(
        query="test query",
        vertical=vertical,
        provider_chain=[provider],
        hits=[
            SearchHit(
                title="Result One",
                url="https://example.com/article",
                snippet="Short snippet",
                domain="example.com",
                provider=provider,
            )
        ],
        warnings=[],
        quota_state={"serper_calls": 1, "serper_limit": 2500},
    )


class RetrievalServiceContractTest(unittest.TestCase):
    def test_general_search_uses_serper_when_available(self):
        with patch.dict("os.environ", {"SERPER_API_KEY": "x"}, clear=False):
            with patch("backend.retrieval.service.can_use_serper", return_value=True):
                with patch("backend.retrieval.service._search_serper", return_value=_response("serper")) as serper:
                    with patch("backend.retrieval.service._search_ddg_text") as ddg:
                        response = search_web(SearchRequest(query="data scientist"))
        self.assertEqual(response.provider_chain, ["serper"])
        serper.assert_called_once()
        ddg.assert_not_called()

    def test_general_search_falls_back_to_ddg(self):
        with patch.dict("os.environ", {"SERPER_API_KEY": "x"}, clear=False):
            with patch("backend.retrieval.service.can_use_serper", return_value=True):
                with patch("backend.retrieval.service._search_serper", side_effect=RuntimeError("boom")):
                    with patch("backend.retrieval.service._search_ddg_text", return_value=_response("ddg_text")) as ddg:
                        response = search_web(SearchRequest(query="data scientist"))
        self.assertEqual(response.provider_chain, ["ddg_text"])
        self.assertTrue(any("Serper failed" in warning for warning in response.warnings))
        ddg.assert_called_once()

    def test_news_search_uses_ddg_news(self):
        with patch("backend.retrieval.service._search_ddg_news", return_value=_response("ddg_news", "news")) as news:
            response = search_web(SearchRequest(query="ai news", vertical="news"))
        self.assertEqual(response.vertical, "news")
        self.assertEqual(response.provider_chain, ["ddg_news"])
        news.assert_called_once()

    def test_reddit_search_falls_back_without_credentials(self):
        with patch("backend.retrieval.service._search_reddit_praw", side_effect=RuntimeError("no creds")):
            with patch(
                "backend.retrieval.service._search_reddit_fallback",
                return_value=_response("ddg_text_reddit_fallback", "reddit"),
            ) as fallback:
                response = search_reddit(SearchRequest(query="llm careers", vertical="reddit"))
        self.assertEqual(response.vertical, "reddit")
        self.assertTrue(any("PRAW unavailable" in warning for warning in response.warnings))
        fallback.assert_called_once()

    def test_search_formatter_includes_results_and_quota(self):
        text = format_search_response(_response("serper"))
        self.assertIn("Provider chain: serper", text)
        self.assertIn("Quota: serper_calls=1/2500", text)
        self.assertIn("Result One", text)


if __name__ == "__main__":
    unittest.main()
