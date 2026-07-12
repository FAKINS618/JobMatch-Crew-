from tavily import TavilyClient
from app.config import settings



def search_jobs(query: str, max_results: int = 5):
    if not settings.tavily_api_key:
        raise ValueError("TAVILY_API_KEY is not configured")

    client = TavilyClient(api_key=settings.tavily_api_key)

    response = client.search(
        query=query,
        max_results=max_results,
        search_depth="basic",
    )

    results = response.get("results", [])

    return [
        {
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("content"),
            "source": "tavily",
        }
        for item in results
    ]