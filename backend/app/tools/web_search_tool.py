import logging
from typing import Literal
from tavily import TavilyClient
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
tavily_client = TavilyClient()


@tool
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """
    Search the internet for information.

    Args:
        query: The search query string
        max_results: The maximum number of search results to return


    Returns:
        Search results as a dict
    """
    try:
        logger.info("Searching for: %s (max_results=%d, topic=%s)", query, max_results, topic)
        results = tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic,
        )
        logger.info("Search returned %d results", len(results.get("results", [])) if isinstance(results, dict) else 0)
        return results
    except Exception as e:
        logger.exception("Search failed for query '%s': %s", query, e)
        raise