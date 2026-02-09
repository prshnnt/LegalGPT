from typing import Literal
from tavily import TavilyClient
from langchain_core.tools import tool
from dotenv import load_dotenv
load_dotenv()

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
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )