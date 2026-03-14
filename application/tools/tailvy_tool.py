import os

from tavily import TavilyClient


def search_web(query: str, max_results: int = 5) -> list[dict]:
    client = TavilyClient(api_key=os.getenv("TAILVY_API_KEY"))
    response = client.search(query, max_results=max_results)

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0.0),
        }
        for r in response.get("results", [])
    ]
