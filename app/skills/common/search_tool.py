import json
import os
from typing import Any, Dict, List, Optional

from langchain_core.tools import Tool
from langchain_community.tools import DuckDuckGoSearchResults, DuckDuckGoSearchRun
from langchain_community.tools.tavily_search import TavilySearchResults

from app.skills.rag.rag_engine import search_knowledge as rag_search_knowledge
from app.infrastructure.config.settings import settings


class SearchToolFactory:
    @staticmethod
    def get_search_tool(return_results_obj=False):
        """
        根据配置返回合适的搜索工具。

        Args:
            return_results_obj: 如果为 True，返回 SearchResults 对象（用于 Consultant，需要元数据）。
                                如果为 False，返回 SearchRun 对象（用于 Radar/Politics，只需文本）。
                                注意：TavilySearchResults 返回的是结构化列表，既可以用作 Run 也可以用作 Results。
        """
        config = settings.search
        provider = config.provider
        tavily_key = config.tavily_api_key or os.getenv("TAVILY_API_KEY")

        if provider == "tavily" or (tavily_key and provider != "duckduckgo"):
            if tavily_key:
                print("Using Tavily Search Tool")
                return TavilySearchResults(tavily_api_key=tavily_key, max_results=5)
            else:
                print("Warning: Tavily provider selected but no key found. Fallback to DuckDuckGo.")

        print("Using DuckDuckGo Search Tool")
        if return_results_obj:
            return DuckDuckGoSearchResults()
        else:
            return DuckDuckGoSearchRun()


def get_search_tool(return_results_obj=False):
    return SearchToolFactory.get_search_tool(return_results_obj)


async def search_knowledge(
    query: str,
    top_k: int = 5,
    subject: Optional[str] = None,
    question_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search for knowledge from the knowledge base.

    Args:
        query: The search query.
        top_k: The number of results to return.
        subject: The subject to filter by.
        question_type: The question type to filter by.

    Returns:
        A list of knowledge entries.
    """
    return await rag_search_knowledge(query, top_k, subject, question_type)


async def search_internet(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """Search the internet for information.

    Args:
        query: The search query.
        num_results: The number of results to return.

    Returns:
        A list of search results.
    """
    # TODO: Implement internet search
    # For now, return an empty list
    return []
