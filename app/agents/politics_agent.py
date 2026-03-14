import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.skills.common.search_tool import get_search_tool
import datetime
from app.runtime.llm import get_llm

class PoliticsNewsItem(BaseModel):
    title: str = Field(description="新闻标题。")
    summary: str = Field(description="详细的新闻摘要，包含背景、起因、经过和结果（来龙去脉）。")
    exam_point: str = Field(description="该新闻在考研政治中的具体考点（如：马原-矛盾普遍性，毛中特-高质量发展）。")
    source_url: Optional[str] = Field(description="新闻来源 URL（如果可用）。")

class PoliticsAlertMessage(BaseModel):
    has_relevant_news: bool = Field(description="如果有值得考研政治关注的时政新闻，则为 True。")
    news_items: List[PoliticsNewsItem] = Field(description="相关新闻列表。")

def check_politics_news() -> PoliticsAlertMessage:
    """
    检查当天适合考研政治的时政新闻。
    """
    search_tool = get_search_tool(return_results_obj=False)

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")

    queries = [
        f"时政新闻 {today_str}",
        f"考研政治 热点 {today_str}",
        f"中国 重大新闻 {today_str}",
    ]

    combined_results = ""
    for q in queries:
        try:
            res = search_tool.invoke(q)
            combined_results += f"Query: {q}\nResult: {res}\n---\n"
        except Exception as e:
            print(f"Search error for {q}: {e}")

    if not combined_results:
        return PoliticsAlertMessage(has_relevant_news=False, news_items=[])

    llm = get_llm(temperature=0)

    analyzer = llm.with_structured_output(PoliticsAlertMessage)

    system_template = """你是一位考研政治辅导专家。
    请分析当天的搜索结果，筛选出对【考研政治】考试有价值的时政新闻。

    筛选标准：
    1. 涉及国家大政方针、中央重要会议（如全会、经济工作会议）。
    2. 习近平总书记的重要讲话、考察活动或回信。
    3. 重大国际外交事件（涉及中国）。
    4. 具有里程碑意义的科技成就或社会事件。

    输出要求：
    - 返回一个 JSON 对象，其中包含 'has_relevant_news' (bool) 和 'news_items' (list)。
    - 如果没有有价值新闻，has_relevant_news=False，news_items 为空列表。
    - 如果有价值新闻，has_relevant_news=True。
    - 'news_items' 列表中的每一项必须包含 'title', 'summary', 'exam_point', 'source_url'。

    字段详情：
    - title: 简练的新闻标题。
    - summary: 详细的新闻摘要，包含背景、起因、经过和结果（来龙去脉）。
    - exam_point: 指出该新闻对应的考研政治考点（如：体现了什么哲学原理或毛中特思想）。
    - source_url: 来源链接，如果未明确提供，留空或设为 null。

    语言：简体中文。
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("human", "Search Results:\n{results}")
    ])

    chain = prompt | analyzer

    try:
        alert = chain.invoke({"results": combined_results})
        return alert
    except Exception as e:
        print(f"Analysis Failed: {e}")
        return PoliticsAlertMessage(has_relevant_news=False, news_items=[])
