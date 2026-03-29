import pytest
from unittest.mock import MagicMock, patch

from application.agent.nodes import generate_answer, retrieve_docs, search_web
from application.models.schemas import SourceDocument


def make_state(query="test query", max_results=3, search_results=None, retrieved_docs=None):
    return {
        "query": query,
        "max_results": max_results,
        "search_results": search_results or [],
        "retrieved_docs": retrieved_docs or [],
        "steps": [],
        "answer": "",
    }


class TestSearchWebNode:
    def test_returns_search_results(self):
        fake_results = [
            {"title": "Article", "url": "http://x.com", "content": "body", "score": 0.9}
        ]
        with patch("application.agent.nodes.tavily_search", return_value=fake_results):
            output = search_web(make_state(query="AI news", max_results=1))

        assert output["search_results"] == fake_results

    def test_step_message_is_added(self):
        with patch("application.agent.nodes.tavily_search", return_value=[]):
            output = search_web(make_state())
        assert len(output["steps"]) == 1
        assert "Searched web" in output["steps"][0]

    def test_max_results_is_passed_to_tavily(self):
        with patch("application.agent.nodes.tavily_search", return_value=[]) as mock_search:
            search_web(make_state(max_results=7))
        mock_search.assert_called_once_with("test query", max_results=7)


class TestRetrieveDocsNode:
    def test_returns_retrieved_docs(self):
        fake_doc = SourceDocument(text="relevant text", source="db", score=0.85)
        with patch("application.agent.nodes.store") as mock_store:
            mock_store.query.return_value = [fake_doc]
            output = retrieve_docs(make_state())

        assert output["retrieved_docs"] == [fake_doc]

    def test_step_message_is_added(self):
        with patch("application.agent.nodes.store") as mock_store:
            mock_store.query.return_value = []
            output = retrieve_docs(make_state())
        assert len(output["steps"]) == 1
        assert "Retrieved" in output["steps"][0]

    def test_queries_with_k_equals_5(self):
        with patch("application.agent.nodes.store") as mock_store:
            mock_store.query.return_value = []
            retrieve_docs(make_state(query="deep learning"))
        mock_store.query.assert_called_once_with("deep learning", k=5)


class TestGenerateAnswerNode:
    def _make_cohere_response(self, text: str) -> MagicMock:
        content_block = MagicMock()
        content_block.text = text
        message = MagicMock()
        message.content = [content_block]
        response = MagicMock()
        response.message = message
        return response

    def test_returns_answer(self):
        fake_response = self._make_cohere_response("The answer is 42.")
        with patch("application.agent.nodes._co") as mock_co:
            mock_co.chat.return_value = fake_response
            output = generate_answer(make_state(query="What is the answer?"))

        assert output["answer"] == "The answer is 42."

    def test_step_message_is_added(self):
        fake_response = self._make_cohere_response("answer")
        with patch("application.agent.nodes._co") as mock_co:
            mock_co.chat.return_value = fake_response
            output = generate_answer(make_state())
        assert len(output["steps"]) == 1
        assert "Generated" in output["steps"][0]

    def test_context_includes_web_and_docs(self):
        fake_response = self._make_cohere_response("answer")
        state = make_state(
            query="question",
            search_results=[{"title": "Web Article", "content": "web content"}],
            retrieved_docs=[SourceDocument(text="stored text", source="db", score=0.9)],
        )
        with patch("application.agent.nodes._co") as mock_co:
            mock_co.chat.return_value = fake_response
            generate_answer(state)

        call_args = mock_co.chat.call_args
        prompt = call_args.kwargs["messages"][0]["content"]
        assert "Web Article" in prompt
        assert "stored text" in prompt
