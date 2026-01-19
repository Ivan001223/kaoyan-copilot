import os
from langchain_core.tools import Tool
from langchain_community.tools import DuckDuckGoSearchResults, DuckDuckGoSearchRun
from langchain_community.tools.tavily_search import TavilySearchResults

from app.core.config_manager import config_manager

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
        config = config_manager.get_config().get("search", {})
        provider = config.get("provider", "duckduckgo")
        tavily_key = config.get("tavily_api_key") or os.getenv("TAVILY_API_KEY")
        
        # 优先检查 Tavily 配置
        if provider == "tavily" or (tavily_key and provider != "duckduckgo"):
            if tavily_key:
                print("Using Tavily Search Tool")
                # TavilySearchResults 返回的是 List[Dict]，包含 url, content
                return TavilySearchResults(tavily_api_key=tavily_key, max_results=5)
            else:
                print("Warning: Tavily provider selected but no key found. Fallback to DuckDuckGo.")
        
        # 默认 DuckDuckGo
        print("Using DuckDuckGo Search Tool")
        if return_results_obj:
            return DuckDuckGoSearchResults()
        else:
            return DuckDuckGoSearchRun()

# Global instance helper
def get_search_tool(return_results_obj=False):
    return SearchToolFactory.get_search_tool(return_results_obj)
